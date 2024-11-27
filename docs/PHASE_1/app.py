import os
from flask import Flask, jsonify, request
import xrpl
import time
import sqlite3
import requests
from threading import Thread

app = Flask(__name__)
testnet_url = "https://s.altnet.rippletest.net:51234"
client = xrpl.clients.JsonRpcClient(testnet_url)
DATABASE = 'transactions.db'

#Ensure the database exists
def init_db():
    conn = sqlite3.connect(DATABASE)
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
    conn.close()

init_db()

merchant_address = os.environ.get("MERCHANT_ADDRESS")

transactions = []

def monitor_payments():
    global transactions
    while True:
        try:
            account_tx = client.request(xrpl.models.requests.AccountTx(account=merchant_address, ledger_index="validated")).result
            new_transactions = account_tx["transactions"]
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()

            for tx in new_transactions:
                tx_hash = tx['tx']['hash']
                #Check if transaction already exists
                cursor.execute("SELECT * FROM transactions WHERE tx_hash = ?", (tx_hash,))
                existing_tx = cursor.fetchone()
                if not existing_tx:
                    amount = float(tx['meta']['delivered_amount'])/1000000 #convert to XRP
                    #process transaction (add fiat conversion here later)
                    cursor.execute('''
                        INSERT INTO transactions (tx_hash, amount, fiat_amount, fiat_currency, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (tx_hash, amount, 0, "USD", time.strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    print(f"New transaction added to database: {tx_hash}")


            conn.close()
        except Exception as e:
            print(f"Error monitoring payments: {e}")
        time.sleep(5)

def get_xrp_to_usd_rate():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': 'YOUR_COINMARKETCAP_API_KEY'}
    try:
        response = requests.get(url, headers=headers, params=parameters)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data['data']['XRP']['quote']['USD']['price']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching XRP rate: {e}")
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
