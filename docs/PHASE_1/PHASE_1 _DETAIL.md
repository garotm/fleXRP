# Phase 1 step-by-step

Since we're using Flask, we'll need to integrate these components into a Flask application. We'll focus on functionality first, then address error handling and more robust features later.

## Step 1.1: XRPL Account Setup (Flask Integration)

This step doesn't directly involve Flask. We'll generate the wallet information outside the Flask app, then store the relevant data (address, possibly a hashed version of the seed – never store the seed directly in plain text).

### wallet_setup.py (separate file)

```python
from xrpl.wallet import generate_faucet_wallet

testnet_url = "https://s.altnet.rippletest.net:51234"  # Use testnet for development
wallet = generate_faucet_wallet(client=testnet_url, debug=True)

# Securely store the address.  Consider hashing the seed if you must store it.
merchant_address = wallet.classic_address
# ... Secure storage mechanism for merchant_address (e.g., database, environment variable)...

print(f"Merchant Address: {merchant_address}")
```

## Step 1.2: Payment Monitoring (Flask Integration)

We'll create a Flask endpoint that periodically checks for new transactions.

### app.py (main Flask app)

```python
from flask import Flask, jsonify
import xrpl
import time
import os
from threading import Thread

app = Flask(__name__)

# ... Load merchant_address from secure storage ...
merchant_address = os.environ.get("MERCHANT_ADDRESS") #Example, replace with your secure storage

client = xrpl.clients.JsonRpcClient(testnet_url)

transactions = []

def monitor_payments():
    global transactions
    while True:
        try:
            account_tx = client.request(xrpl.models.requests.AccountTx(account=merchant_address, ledger_index="validated")).result
            new_transactions = account_tx["transactions"]
            #Simple check for new transactions - needs refinement in later steps
            if new_transactions and new_transactions != transactions:
                transactions = new_transactions
                for tx in new_transactions:
                    # Process each transaction (later steps will add more detail here)
                    print(f"New transaction detected: {tx}")
        except Exception as e:
            print(f"Error monitoring payments: {e}")
        time.sleep(5)

@app.route('/transactions')
def get_transactions():
    return jsonify(transactions)

if __name__ == '__main__':
    payment_monitor = Thread(target=monitor_payments, daemon=True)
    payment_monitor.start()
    app.run(debug=True)
```

## Step 1.3: Fiat Conversion API Integration (Flask Integration)

Let's use CoinMarketCap (remember to replace YOUR_COINMARKETCAP_API_KEY with your actual key). Error handling is omitted for brevity but should be added.

```python
import requests

def get_xrp_to_usd_rate():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    parameters = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': 'YOUR_COINMARKETCAP_API_KEY'}
    response = requests.get(url, headers=headers, params=parameters)
    data = response.json()
    return data['data']['XRP']['quote']['USD']['price']

# ...in app.py...
@app.route('/xrp_rate')
def get_xrp_rate():
    rate = get_xrp_to_usd_rate()
    return jsonify({'rate':rate})
```

## Step 1.4: Fiat Calculation (Flask Integration)

This is a simple function that can be called from other parts of the application.

```python
def calculate_fiat_amount(xrp_amount, exchange_rate):
    return xrp_amount * exchange_rate
```

## Next Steps and Improvements:

* **Robust Transaction Processing:** The monitor_payments function needs significant improvement. We need to:
  * Properly identify new transactions (avoid duplicates).
  * Validate transaction details (ensure it's a payment to the merchant).
  * Store transaction data persistently (database).
* **Error Handling:** Add comprehensive error handling to all functions.
* **Security:** Implement proper security measures for API keys and sensitive data. Use environment variables or secure configuration mechanisms.
* **Database Integration:** Use a database (e.g., SQLite, PostgreSQL) to store transaction data, merchant information, and settings.
* **Flask Template:** Create a basic Flask template to display transaction information.

This expanded response provides a more complete and practical starting point. Remember to install the necessary libraries (`flask`, `requests`, `xrpl-py`). This is still a simplified version, and further development will be needed to create a production-ready system. Remember to replace placeholder values like API keys and addresses with your actual credentials.
