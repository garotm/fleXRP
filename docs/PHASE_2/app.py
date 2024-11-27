"""
XRPL Payment Monitoring Service

This module implements a Flask-based service for monitoring XRPL payments,
converting XRP amounts to USD, and storing transaction details securely.
It provides REST endpoints for retrieving transaction data and current exchange rates.
"""

import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging.handlers
from pathlib import Path
from decimal import Decimal
import sqlite3
from contextlib import contextmanager
from threading import Thread, Event

import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx
from flask import Flask, jsonify, Response
import requests
from requests.exceptions import RequestException

# Application Configuration
class Config:
    """Application configuration settings."""
    TESTNET_URL: str = "https://s.altnet.rippletest.net:51234"
    DATABASE: Path = Path("data/payments.db")
    LOG_FILE: Path = Path("logs/fleXRP.log")
    MIN_XRP_AMOUNT: Decimal = Decimal("0.0001")
    REQUEST_TIMEOUT: int = 30
    RATE_LIMIT_RETRIES: int = 3
    POLLING_INTERVAL: int = 5

# Ensure required directories exist
Config.DATABASE.parent.mkdir(parents=True, exist_ok=True)
Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    handlers=[
        logging.handlers.RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=10485760,  # 10MB
            backupCount=5
        ),
        logging.StreamHandler()
    ],
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
client = JsonRpcClient(Config.TESTNET_URL)

# Environment variable validation
REQUIRED_ENV_VARS = ["MERCHANT_ADDRESS", "COINMARKETCAP_API_KEY"]
missing_vars = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

merchant_address: str = os.environ["MERCHANT_ADDRESS"]
coinmarketcap_api_key: str = os.environ["COINMARKETCAP_API_KEY"]

# Thread control
shutdown_event = Event()

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(Config.DATABASE)
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        if conn:
            conn.close()

def init_db() -> None:
    """Initialize the SQLite database with required tables."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE,
                sender TEXT,
                receiver TEXT,
                amount_xrp DECIMAL(20, 6),
                amount_usd DECIMAL(20, 2),
                timestamp TEXT,
                status TEXT DEFAULT 'pending'
            )
        ''')
        conn.commit()

def is_valid_payment(transaction: Dict[str, Any], merchant_addr: str) -> bool:
    """
    Validate if a transaction is a valid payment.

    Args:
        transaction: Transaction data from XRPL
        merchant_addr: Merchant's XRPL address

    Returns:
        bool: True if payment is valid, False otherwise
    """
    try:
        if (transaction['tx'].get('TransactionType') != 'Payment' or
            transaction['tx'].get('Destination') != merchant_addr):
            return False
        
        amount = Decimal(str(transaction['meta']['delivered_amount'])) / Decimal("1000000")
        return amount >= Config.MIN_XRP_AMOUNT
    except (KeyError, TypeError, ValueError) as e:
        logger.warning(f"Invalid transaction format: {e}", exc_info=True)
        return False

def store_transaction(
    tx_hash: str,
    sender: str,
    receiver: str,
    xrp_amount: Decimal,
    usd_amount: Decimal
) -> bool:
    """
    Store transaction details in the database.

    Args:
        tx_hash: Transaction hash
        sender: Sender's address
        receiver: Receiver's address
        xrp_amount: Amount in XRP
        usd_amount: Amount in USD

    Returns:
        bool: True if storage successful, False otherwise
    """
    try:
        with get_db_connection() as conn:
            conn.execute('''
                INSERT INTO payments (
                    tx_hash, sender, receiver, amount_xrp,
                    amount_usd, timestamp, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tx_hash, sender, receiver, xrp_amount,
                usd_amount, datetime.utcnow().isoformat(),
                'confirmed'
            ))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error storing transaction {tx_hash}: {e}", exc_info=True)
        return False

def get_xrp_to_usd_rate() -> Optional[Decimal]:
    """
    Fetch current XRP to USD exchange rate from CoinMarketCap.

    Returns:
        Optional[Decimal]: Exchange rate or None if fetch fails
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': coinmarketcap_api_key
    }
    
    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        return Decimal(str(data['data']['XRP']['quote']['USD']['price']))
    except (RequestException, KeyError, ValueError) as e:
        logger.error(f"Error fetching XRP rate: {e}", exc_info=True)
        return None

def monitor_payments() -> None:
    """Monitor XRPL for incoming payments to merchant address."""
    processed_transactions = set()
    
    while not shutdown_event.is_set():
        try:
            response = client.request(AccountTx(
                account=merchant_address,
                ledger_index="validated"
            )).result
            
            for tx in response['transactions']:
                tx_hash = tx['tx']['hash']
                if tx_hash not in processed_transactions:
                    if is_valid_payment(tx, merchant_address):
                        xrp_amount = Decimal(str(tx['meta']['delivered_amount'])) / Decimal("1000000")
                        usd_amount = Decimal("0")
                        
                        rate = get_xrp_to_usd_rate()
                        if rate:
                            usd_amount = xrp_amount * rate
                        
                        if store_transaction(
                            tx_hash,
                            tx['tx']['Account'],
                            merchant_address,
                            xrp_amount,
                            usd_amount
                        ):
                            processed_transactions.add(tx_hash)
                            logger.info(f"Processed transaction: {tx_hash}")
            
            shutdown_event.wait(Config.POLLING_INTERVAL)
            
        except Exception as e:
            logger.error("Error in payment monitoring:", exc_info=True)
            shutdown_event.wait(Config.POLLING_INTERVAL * 2)

@app.route('/transactions')
def get_transactions() -> Response:
    """
    API endpoint to retrieve all transactions.

    Returns:
        Response: JSON response containing transaction list
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM payments ORDER BY timestamp DESC")
            transactions = cursor.fetchall()
        
        return jsonify([dict(tx) for tx in transactions])
    except Exception as e:
        logger.error("Error retrieving transactions:", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/xrp_rate')
def get_xrp_rate() -> Response:
    """
    API endpoint to retrieve current XRP/USD rate.

    Returns:
        Response: JSON response containing current rate
    """
    rate = get_xrp_to_usd_rate()
    if rate:
        return jsonify({'rate': float(rate)})
    return jsonify({'error': 'Could not fetch XRP rate'}), 500

def cleanup() -> None:
    """Cleanup resources before shutdown."""
    shutdown_event.set()
    logger.info("Shutting down payment monitor...")

if __name__ == '__main__':
    init_db()
    payment_monitor = Thread(target=monitor_payments, daemon=True)
    payment_monitor.start()
    
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        cleanup()
