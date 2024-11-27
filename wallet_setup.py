import os
from xrpl.wallet import generate_faucet_wallet
import hashlib

def generate_and_store_wallet(testnet_url="https://s.altnet.rippletest.net:51234"):
    """Generates an XRPL wallet and securely stores the address.  Never directly stores the seed."""
    try:
        wallet = generate_faucet_wallet(client=testnet_url, debug=True)
        address = wallet.classic_address
        seed_hash = hashlib.sha256(wallet.seed.encode()).hexdigest() #Hash the seed for storage

        #Store in environment variables (for this example) -  replace with a more secure method like a database.
        os.environ["MERCHANT_ADDRESS"] = address
        os.environ["SEED_HASH"] = seed_hash #Store a hash, not the actual seed

        print(f"Merchant Address: {address}")
        print(f"Seed Hash (for verification): {seed_hash}") #Only use this hash for later verification
        return address

    except Exception as e:
        print(f"Error generating wallet: {e}")
        return None

if __name__ == "__main__":
    generate_and_store_wallet()
