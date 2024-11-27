"""
XRPL Payment Monitoring Module

This module implements a robust payment monitoring system for the XRPL network.
It handles transaction validation, filtering, and persistent storage of payment data.
The module includes comprehensive error handling, transaction validation, and
secure database operations.

Dependencies:
    - xrpl-py: For XRPL network interaction
    - sqlite3: For persistent storage
    - requests: For external API calls
"""

import os
from typing import Optional, Dict, Any, Set
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from decimal import Decimal
import sqlite3
from contextlib import contextmanager
import time
from threading import Event

import xrpl
from xrpl.clients import JsonRpcClient, XRPLRequestError
from xrpl.models.requests import AccountTx

# Configuration
class Config:
    """Application configuration and constants."""
    
    DATABASE: Path = Path('data/payments.db')
    LOG_FILE: Path = Path('logs/fleXRP.log')
    MIN_XRP_AMOUNT: Decimal = Decimal('0.0001')
    POLLING_INTERVAL: int = 5
    RETRY_DELAY: int = 10
    MAX_RETRIES: int = 3
    
    # Ensure required directories exist
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure logging with rotation
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(
    Config.LOG_FILE,
    maxBytes=10_485_760,  # 10MB
    backupCount=5
)
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)

# Global shutdown event for graceful termination
shutdown_event = Event()

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection object
    
    Raises:
        sqlite3.Error: If database connection fails
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
    """
    Initialize the SQLite database with required tables and indices.
    
    Creates the payments table if it doesn't exist and sets up necessary indices
    for optimal query performance.
    
    Raises:
        sqlite3.Error: If database initialization fails
    """
    try:
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
            # Create indices for frequent queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_tx_hash ON payments(tx_hash)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON payments(timestamp)')
            conn.commit()
    except sqlite3.Error as e:
        logger.error("Database initialization failed", exc_info=True)
        raise

def is_valid_payment(transaction: Dict[str, Any], merchant_address: str) -> bool:
    """
    Validate if a transaction is a valid payment to the merchant.
    
    Args:
        transaction: Transaction data from XRPL
        merchant_address: Merchant's XRPL address
    
    Returns:
        bool: True if payment is valid, False otherwise
    """
    try:
        if not all(k in transaction for k in ['tx', 'meta']):
            return False
            
        tx_data = transaction['tx']
        if (tx_data.get('TransactionType') != 'Payment' or
            tx_data.get('Destination') != merchant_address):
            return False
        
        amount = Decimal(str(transaction['meta']['delivered_amount'])) / Decimal('1000000')
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
    Store transaction data in the database.
    
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
                tx_hash,
                sender,
                receiver,
                xrp_amount,
                usd_amount,
                datetime.utcnow().isoformat(),
                'confirmed'
            ))
            conn.commit()
        return True
    except sqlite3.Error as e:
        logger.error(f"Database error storing transaction {tx_hash}: {e}", exc_info=True)
        return False

def convert_xrp_to_usd(xrp_amount: Decimal) -> Decimal:
    """
    Convert XRP amount to USD using current exchange rate.
    
    Args:
        xrp_amount: Amount in XRP
    
    Returns:
        Decimal: Amount in USD, 0 if conversion fails
    """
    try:
        rate = get_xrp_to_usd_rate()
        return xrp_amount * Decimal(str(rate)) if rate else Decimal('0')
    except (TypeError, ValueError) as e:
        logger.error(f"Error converting XRP to USD: {e}", exc_info=True)
        return Decimal('0')

def monitor_payments(address: str) -> None:
    """
    Monitor XRPL for incoming payments to specified address.
    
    Continuously monitors the XRPL for new payments, validates them,
    and stores valid transactions in the database.
    
    Args:
        address: XRPL address to monitor
    """
    processed_transactions: Set[str] = set()
    client = JsonRpcClient(os.getenv('XRPL_NODE_URL', 'https://s.altnet.rippletest.net:51234'))
    
    logger.info(f"Starting payment monitoring for address: {address}")
    
    while not shutdown_event.is_set():
        try:
            response = client.request(AccountTx(
                account=address,
                ledger_index="validated"
            )).result
            
            for tx in response['transactions']:
                tx_hash = tx['tx']['hash']
                if tx_hash not in processed_transactions:
                    try:
                        if is_valid_payment(tx, address):
                            xrp_amount = Decimal(str(tx['meta']['delivered_amount'])) / Decimal('1000000')
                            usd_amount = convert_xrp_to_usd(xrp_amount)
                            
                            if store_transaction(
                                tx_hash,
                                tx['tx']['Account'],
                                address,
                                xrp_amount,
                                usd_amount
                            ):
                                processed_transactions.add(tx_hash)
                                logger.info(f"Processed transaction: {tx_hash}")
                    except Exception as e:
                        logger.error(f"Error processing transaction {tx_hash}: {e}", exc_info=True)
            
            shutdown_event.wait(Config.POLLING_INTERVAL)
            
        except XRPLRequestError as e:
            logger.error(f"XRPL Error: {e}", exc_info=True)
            shutdown_event.wait(Config.RETRY_DELAY)
        except Exception as e:
            logger.error("Unexpected error in monitor_payments", exc_info=True)
            shutdown_event.wait(Config.RETRY_DELAY)

def cleanup() -> None:
    """Perform cleanup operations before shutdown."""
    shutdown_event.set()
    logger.info("Payment monitoring stopped")

if __name__ == '__main__':
    try:
        init_db()
        merchant_address = os.environ.get('MERCHANT_ADDRESS')
        if not merchant_address:
            raise ValueError("MERCHANT_ADDRESS environment variable not set")
        
        monitor_payments(merchant_address)
    except KeyboardInterrupt:
        logger.info("Shutting down payment monitor...")
    except Exception as e:
        logger.error("Fatal error in payment monitor", exc_info=True)
    finally:
        cleanup()
