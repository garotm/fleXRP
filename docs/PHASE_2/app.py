'''
The primary changes will be within app.py, specifically to the monitor_payments function, also provided seperately.
wallet_setup.py remains unchanged, as it only handles wallet generation.
'''

import os
from flask import Flask, jsonify, request
import xrpl
import time
import sqlite3
import requests
from threading import Thread
import logging
import json

app = Flask(__name__)
testnet_url = "https://s.altnet.rippletest.net:51234"
client = xrpl.clients.JsonRpcClient(testnet_url)
DATABASE = 'payments.db' #Changed database name to payments.db
COINMARKETCAP_API_KEY = os.environ.get("COINMARKETCAP_API_KEY")
logging.basicConfig(filename='fleXRP.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Database Initialization (modified to match new table)
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tx_hash TEXT UNIQUE,
            sender TEXT,
            receiver TEXT,
            amount_xrp REAL,
            amount_usd REAL,
            timestamp TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

merchant_address = os.environ.get("MERCHANT_ADDRESS")
processed_transactions = set() #Keep track of processed transactions

def monitor_payments():
    global processed_transactions
    while True:
        try:
            transactions = client.request(xrpl.models.requests.AccountTx(account=merchant_address,ledger_index="validated")).result
            for tx in transactions['transactions']:
                tx_hash = tx['tx']['hash']
                if tx_hash not in processed_transactions:
                    try:
                        if is_valid_payment(tx, merchant_address):
                            xrp_amount = float(tx['meta']['delivered_amount'])/1000000
                            usd_amount = convert_xrp_to_usd(xrp_amount)
                            store_transaction(tx_hash, tx['tx']['Account'], merchant_address, xrp_amount, usd_amount)
                            processed_transactions.add(tx_hash)
                            print(f"Processed transaction: {tx_hash}")
                    except Exception as e:
                        logging.exception(f"Error processing transaction {tx_hash}: {e}")

            time.sleep(5)
        except xrpl.clients.XRPLRequestError as e:
            logging.error(f"XRPL Error: {e}")
            time.sleep(10)
        except Exception as e:
            logging.exception(f"Error in monitor_payments: {e}")

def is_valid_payment(transaction, merchant_address):
    try:
        if transaction['TransactionType'] != 'Payment':
            return False
        if transaction['tx']['Destination'] != merchant_address:
            return False
        if float(transaction['meta']['delivered_amount'])/1000000 < 0.0001:
            return False
        # Add more validation checks as needed
        return True
    except (KeyError, TypeError) as e:
        logging.warning(f"Invalid transaction format: {e}")
        return False

def store_transaction(tx_hash, sender, receiver, xrp_amount, usd_amount):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (tx_hash, sender, receiver, amount_xrp, amount_usd, timestamp, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tx_hash, sender, receiver, xrp_amount, usd_amount, time.strftime('%Y-%m-%d %H:%M:%S'), 'confirmed'))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Database error storing transaction {tx_hash}: {e}")

def convert_xrp_to_usd(xrp_amount):
    rate = get_xrp_to_usd_rate()
    if rate:
        return xrp_amount * rate
    else:
        return 0

def get_xrp_to_usd_rate():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': COINMARKETCAP_API_KEY}
    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status()
        data = response.json()
        return data['data']['XRP']['quote']['USD']['price']
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching XRP rate: {e}")
        return None

@app.route('/transactions')
def get_transactions():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    conn.close()
    return jsonify([{'tx_hash':row[1], 'amount':row[2], 'fiat_amount':row[3], 'currency':row[4]} for row in transactions])

@app.route('/xrp_rate')
def get_xrp_rate():
    rate = get_xrp_to_usd_rate()
    if rate:
        return jsonify({'rate': rate})
    else:
        return jsonify({'error':'Could not fetch XRP rate'}), 500

if __name__ == '__main__':
    payment_monitor = Thread(target=monitor_payments, daemon=True)
    payment_monitor.start()
    app.run(debug=True)
