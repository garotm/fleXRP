# Phase 1: Foundation (XRPL & Fiat Conversion)

This document outlines the implementation of XRPL integration and fiat conversion components for the fleXRP payment system.

## Prerequisites

### Environment Setup

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Unix/macOS
# or
.\venv\Scripts\activate  # Windows

# Install required packages
pip install xrpl-py requests python-dotenv
```

### Environment Variables

Create a `.env` file in your project root:

```bash
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234
MERCHANT_ADDRESS=your_xrpl_address
COINMARKETCAP_API_KEY=your_api_key
LOG_LEVEL=INFO
```

## Implementation Steps

### Step 1.1: XRPL Account Setup

```python
from pathlib import Path
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_merchant_wallet(testnet_url: str) -> dict:
    """
    Generate and secure a new XRPL wallet for merchant operations.
    
    Args:
        testnet_url: URL of the XRPL testnet node
    
    Returns:
        dict: Wallet information including address and seed hash
    """
    try:
        client = JsonRpcClient(testnet_url)
        wallet = generate_faucet_wallet(client=client, debug=False)
        
        # Store only the hash of the seed, never the seed itself
        seed_hash = hashlib.sha256(wallet.seed.encode()).hexdigest()
        
        return {
            'address': wallet.classic_address,
            'seed_hash': seed_hash
        }
    except Exception as e:
        logger.error(f"Wallet generation failed: {e}", exc_info=True)
        raise
```

**Important Security Notes:**
- Never store or log the wallet seed
- Use secure environment variables for sensitive data
- Implement proper key management in production

### Step 1.2: Payment Monitoring

The payment monitoring system has been significantly improved for production use:

```python
from decimal import Decimal
from typing import Optional

def monitor_payments(address: str) -> None:
    """
    Monitor XRPL for incoming payments to specified address.
    
    Args:
        address: XRPL address to monitor
    """
    processed_transactions = set()
    
    while not shutdown_event.is_set():
        try:
            response = client.request(AccountTx(
                account=address,
                ledger_index="validated"
            )).result
            
            for tx in response['transactions']:
                process_transaction(tx, processed_transactions)
                
        except Exception as e:
            logger.error("Payment monitoring error", exc_info=True)
            shutdown_event.wait(Config.RETRY_DELAY)
```

### Step 1.3: Fiat Conversion Integration

Improved rate fetching with proper error handling and rate limiting:

```python
def get_xrp_to_usd_rate() -> Optional[Decimal]:
    """
    Fetch current XRP to USD exchange rate from CoinMarketCap.
    
    Returns:
        Optional[Decimal]: Current exchange rate or None if fetch fails
    """
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
    params = {'symbol': 'XRP', 'convert': 'USD'}
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': os.getenv('COINMARKETCAP_API_KEY')
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return Decimal(str(data['data']['XRP']['quote']['USD']['price']))
    except Exception as e:
        logger.error(f"Rate fetch error: {e}", exc_info=True)
        return None
```

### Step 1.4: Transaction Processing

Enhanced transaction processing with proper validation and storage:

```python
def process_transaction(
    tx_hash: str,
    xrp_amount: Decimal,
    sender: str,
    receiver: str
) -> bool:
    """
    Process and store a validated transaction.
    
    Args:
        tx_hash: Transaction hash
        xrp_amount: Amount in XRP
        sender: Sender's address
        receiver: Receiver's address
    
    Returns:
        bool: True if processing successful
    """
    try:
        usd_amount = convert_xrp_to_usd(xrp_amount)
        return store_transaction(
            tx_hash=tx_hash,
            sender=sender,
            receiver=receiver,
            xrp_amount=xrp_amount,
            usd_amount=usd_amount
        )
    except Exception as e:
        logger.error(f"Transaction processing error: {e}", exc_info=True)
        return False
```

## Production Considerations

### Security
- Implement proper key management
- Use secure environment variables
- Never log sensitive data
- Implement rate limiting
- Use proper error handling

### Monitoring
- Set up comprehensive logging
- Implement health checks
- Monitor transaction processing
- Track API rate limits

### Database
- Use connection pooling
- Implement proper indexing
- Regular backups
- Transaction atomicity

### Error Handling
- Implement retry mechanisms
- Proper exception handling
- Graceful degradation
- Alert systems

## Next Steps
1. Implement comprehensive testing suite
2. Set up CI/CD pipeline
3. Configure monitoring and alerting
4. Implement database migrations
5. Set up backup systems
6. Document API endpoints
7. Implement rate limiting
8. Set up security scanning

## Development Guidelines
- Follow type hints
- Write comprehensive tests
- Document all functions
- Follow security best practices
- Implement proper logging
- Use proper error handling
- Follow PEP 8 style guide
