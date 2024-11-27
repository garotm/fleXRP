import os
from flask import Flask, jsonify, request
import xrpl
import time
import sqlite3
import requests
from threading import Thread
import logging
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import contextmanager

app = Flask(__name__)
testnet_url = "https://s.altnet.rippletest.net:51234"
client = xrpl.clients.JsonRpcClient(testnet_url)
DATABASE = 'transactions.db'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        yield conn
    finally:
        if conn:
            conn.close()

def init_db():
    """
    Initialize the SQLite database and create the transactions table if it does not exist.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_hash TEXT UNIQUE,
                amount REAL,
                fiat_amount REAL,
                fiat_currency TEXT,
                timestamp TEXT
            )
        ''')
        conn.commit()

def monitor_payments():
    """
    Monitor the XRPL account for new transactions and store them in the database.
    Uses marker-based pagination to ensure no transactions are missed.
    """
    marker = None
    while True:
        try:
            request = xrpl.models.requests.AccountTx(
                account=merchant_address,
                ledger_index="validated",
                limit=100  # Process in smaller chunks
            )
            if marker:
                request.marker = marker

            response = client.request(request).result
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for tx in response["transactions"]:
                    tx_hash = tx['tx']['hash']
                    cursor.execute("SELECT 1 FROM transactions WHERE tx_hash = ?", (tx_hash,))
                    if not cursor.fetchone():
                        try:
                            amount = float(tx['meta']['delivered_amount']) / 1000000
                            cursor.execute('''
                                INSERT INTO transactions 
                                (tx_hash, amount, fiat_amount, fiat_currency, timestamp)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                tx_hash, 
                                amount, 
                                0, 
                                "USD", 
                                datetime.utcnow().isoformat()
                            ))
                            conn.commit()
                            logger.info(f"New transaction processed: {tx_hash}")
                        except KeyError as e:
                            logger.error(f"Invalid transaction format: {e}")
                            continue

            marker = response.get("marker")
            if not marker:
                time.sleep(5)  # Only sleep when we've processed all available transactions

        except Exception as e:
            logger.error(f"Error monitoring payments: {e}", exc_info=True)
            time.sleep(10)  # Longer sleep on error to prevent rapid retries

def get_xrp_to_usd_rate() -> Optional[float]:
    """
    Fetch the current XRP to USD exchange rate from CoinMarketCap API.
    Returns:
        Optional[float]: The current exchange rate or None if an error occurs.
    """
    api_key = os.environ.get('CMC_API_KEY')
    if not api_key:
        logger.error("CMC_API_KEY environment variable not set")
        return None

    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': api_key
    }
    
    try:
        response = requests.get(url, headers=headers, params=parameters, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data['data']['XRP']['quote']['USD']['price']
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching XRP rate: {e}", exc_info=True)
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Error parsing XRP rate response: {e}", exc_info=True)
        return None

@app.route('/transactions')
def get_transactions():
    """
    API endpoint to retrieve all transactions from the database.
    Returns:
        Response: JSON response containing a list of transactions.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
    return jsonify([{'tx_hash': row[1], 'amount': row[2], 'fiat_amount': row[3], 'currency': row[4]} for row in transactions])

@app.route('/xrp_rate')
def get_xrp_rate():
    """
    API endpoint to retrieve the current XRP to USD exchange rate.
    Returns:
        Response: JSON response containing the exchange rate or an error message.
    """
    rate = get_xrp_to_usd_rate()
    if rate:
        return jsonify({'rate': rate})
    else:
        return jsonify({'error': 'Could not fetch XRP rate'}), 500

if __name__ == '__main__':
    payment_monitor = Thread(target=monitor_payments, daemon=True)
    payment_monitor.start()
    app.run(debug=True)
