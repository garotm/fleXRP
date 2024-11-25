### Phase 4: Build the Merchant Interface with Flask

**1. Set Up Your Flask Project**

*   **Create Project Structure:**
    *   Create a project folder (e.g., `fleXRP`).
    *   Inside, create the following:
        *   `app.py` (main application file)
        *   `templates/` (folder for HTML templates)
        *   `static/` (folder for CSS, JavaScript files)

*   **Install Flask:**

```bash
pip install Flask
```

**2. Create the `app.py` File**

```python
from flask import Flask, render_template, request, redirect, url_for, session  # Import necessary modules
import xrpl  # For XRPL interactions
import sqlite3  # For database interaction (example)

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Important for session security (change this!)

# --- Helper Functions ---
def get_xrp_balance(address):
    # ... (your existing code to fetch XRP balance from XRPL)

def get_transactions(address):
    # ... (your existing code to fetch transaction history from database)

def generate_qr_code(payment_request):
    # ... (your code to generate QR code from payment request data)

# --- Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ... (handle login logic, authenticate user)
        session['logged_in'] = True  # Set session variable
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # Redirect to login if not logged in

    address = session.get('address')  # Get merchant's address from session
    balance = get_xrp_balance(address)
    transactions = get_transactions(address)
    return render_template('dashboard.html', balance=balance, transactions=transactions)

@app.route('/generate_payment', methods=['POST'])
def generate_payment():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    amount = request.form['amount']
    # ... (generate payment request and QR code)
    qr_code_url = generate_qr_code(payment_request)
    return render_template('payment_qr.html', qr_code_url=qr_code_url)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # ... (handle saving settings to database)
        return redirect(url_for('dashboard'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True)
```

**3. Create Templates**

*   In the `templates/` folder, create HTML files:
    *   `login.html` (login form)
    *   `dashboard.html` (main dashboard with balance, transactions)
    *   `payment_qr.html` (display QR code)
    *   `settings.html` (settings form)

**Example `dashboard.html`:**

```html
<!DOCTYPE html>
<html>
<head>
    <title>fleXRP Dashboard</title>
</head>
<body>
    <h1>Welcome, Merchant!</h1>
    <p>Your XRP balance: {{ balance }}</p>

    <h2>Recent Transactions</h2>
    <table>
        </table>

    <a href="{{ url_for('generate_payment') }}">Generate Payment Request</a>
    <a href="{{ url_for('settings') }}">Settings</a>
</body>
</html>
```

**4. Run the App**

```bash
python app.py
```

**Key Considerations**

*   **Templating:** Use Jinja2 templating in Flask to dynamically generate HTML.
*   **Data Handling:**  Pass data (balance, transactions, etc.) from your Python code to the templates for rendering.
*   **Forms:**  Use Flask's `request` object to handle form submissions (e.g., for payment requests, settings).
*   **Security:**  Implement proper authentication and authorization to protect sensitive data.

This Flask-based structure provides a solid foundation for your fleXRP merchant interface. Remember to fill in the helper functions (`get_xrp_balance`, `get_transactions`, etc.) with your actual logic and design the HTML templates to your liking.
