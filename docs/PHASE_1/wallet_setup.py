"""
XRPL Wallet Generation and Management Module

This module handles the secure generation and storage of XRPL wallets for merchant accounts.
It implements secure practices for handling sensitive wallet information and never stores
private keys directly.
"""

import os
import logging
from typing import Optional, Tuple
from pathlib import Path
import hashlib
from xrpl.wallet import generate_faucet_wallet
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wallet_operations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WalletSetupError(Exception):
    """Custom exception for wallet setup related errors."""
    pass

def validate_testnet_url(url: str) -> bool:
    """
    Validate the provided testnet URL.

    Args:
        url (str): The testnet URL to validate.

    Returns:
        bool: True if URL is valid, False otherwise.
    """
    try:
        client = JsonRpcClient(url)
        # Simple server info request to verify connection
        client.request({
            "command": "server_info"
        })
        return True
    except Exception as e:
        logger.error(f"Failed to validate testnet URL: {e}")
        return False

def secure_hash(data: str) -> str:
    """
    Create a secure hash of the provided data using SHA-256.

    Args:
        data (str): The data to hash.

    Returns:
        str: The hexadecimal representation of the hash.
    """
    return hashlib.sha256(data.encode()).hexdigest()

def generate_and_store_wallet(
    testnet_url: str = "https://s.altnet.rippletest.net:51234",
    env_file: Optional[Path] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates an XRPL wallet and securely stores the address.
    Never directly stores the seed/private key.

    Args:
        testnet_url (str): The URL of the XRPL testnet.
        env_file (Optional[Path]): Path to store environment variables (for development only).

    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing (address, seed_hash) if successful,
                                           (None, None) if failed.

    Raises:
        WalletSetupError: If wallet generation or storage fails.
    """
    try:
        # Validate testnet URL before proceeding
        if not validate_testnet_url(testnet_url):
            raise WalletSetupError("Invalid or unreachable testnet URL")

        # Generate wallet
        wallet: Wallet = generate_faucet_wallet(client=testnet_url, debug=False)
        address: str = wallet.classic_address
        
        # Create secure hash of the seed
        seed_hash: str = secure_hash(wallet.seed)

        # Store in environment variables
        os.environ["MERCHANT_ADDRESS"] = address
        os.environ["SEED_HASH"] = seed_hash

        # Optionally write to .env file (development only)
        if env_file:
            env_file = Path(env_file)
            env_file.parent.mkdir(parents=True, exist_ok=True)
            with env_file.open('a') as f:
                f.write(f"\nMERCHANT_ADDRESS={address}\n")
                f.write(f"SEED_HASH={seed_hash}\n")

        logger.info(f"Wallet generated successfully for address: {address}")
        
        # Verify environment variables were set correctly
        if (os.environ.get("MERCHANT_ADDRESS") != address or 
            os.environ.get("SEED_HASH") != seed_hash):
            raise WalletSetupError("Environment variable verification failed")

        return address, seed_hash

    except Exception as e:
        logger.error(f"Error generating wallet: {str(e)}", exc_info=True)
        raise WalletSetupError(f"Failed to generate wallet: {str(e)}") from e

def verify_wallet_hash(seed: str, stored_hash: str) -> bool:
    """
    Verify a wallet seed against a stored hash.

    Args:
        seed (str): The wallet seed to verify.
        stored_hash (str): The previously stored hash to verify against.

    Returns:
        bool: True if the hash matches, False otherwise.
    """
    return secure_hash(seed) == stored_hash

if __name__ == "__main__":
    try:
        # For development, optionally store in .env file
        env_path = Path(".env")
        address, seed_hash = generate_and_store_wallet(env_file=env_path)
        
        if address and seed_hash:
            logger.info("Wallet setup completed successfully")
            logger.info(f"Merchant Address: {address}")
            logger.info(f"Seed Hash (for verification): {seed_hash}")
        else:
            logger.error("Wallet setup failed")
            exit(1)
    except WalletSetupError as e:
        logger.error(f"Wallet setup failed: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        exit(1)
