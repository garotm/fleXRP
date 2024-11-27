"""
XRPL wallet management service.

This module handles wallet creation, management, and security
for merchant XRPL accounts.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
import json
from cryptography.fernet import Fernet
from xrpl.wallet import Wallet, generate_faucet_wallet
from xrpl.clients import JsonRpcClient

from core.exceptions import XRPLError
from core.error_handlers import with_retry, error_context
from core.metrics import metrics_collector
from core.monitoring import AlertManager

logger = logging.getLogger(__name__)

class WalletService:
    """Service for managing XRPL wallets."""
    
    def __init__(
        self,
        encryption_key: Optional[str] = None,
        storage_path: Optional[Path] = None
    ):
        self.storage_path = storage_path or Path('data/wallets')
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self.encryption_key = encryption_key or os.getenv('WALLET_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key().decode()
            logger.warning("Generated new wallet encryption key")
        
        self.cipher_suite = Fernet(self.encryption_key.encode())
        
        # Initialize metrics
        self.metrics = metrics_collector
    
    @with_retry(max_attempts=3, exceptions=(XRPLError,))
    def create_wallet(
        self,
        merchant_id: str,
        testnet: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new XRPL wallet for a merchant.
        
        Args:
            merchant_id: Unique identifier for the merchant
            testnet: Whether to create wallet on testnet
            
        Returns:
            Dict containing wallet information
            
        Raises:
            XRPLError: If wallet creation fails
        """
        with error_context("create_wallet"):
            with metrics_collector.measure_latency('wallet_creation'):
                try:
                    # Create wallet
                    client = JsonRpcClient(
                        "https://s.altnet.rippletest.net:51234"
                        if testnet else
                        "https://s1.ripple.com:51234"
                    )
                    
                    wallet = generate_faucet_wallet(client) if testnet else Wallet.create()
                    
                    # Prepare wallet data
                    wallet_data = {
                        "merchant_id": merchant_id,
                        "public_key": wallet.public_key,
                        "private_key": wallet.private_key,
                        "classic_address": wallet.classic_address,
                        "testnet": testnet,
                        "active": True
                    }
                    
                    # Encrypt and save wallet
                    self._save_wallet(merchant_id, wallet_data)
                    
                    # Return public information
                    return {
                        "merchant_id": merchant_id,
                        "public_key": wallet.public_key,
                        "classic_address": wallet.classic_address
                    }
                    
                except Exception as e:
                    logger.error(f"Failed to create wallet: {str(e)}", exc_info=True)
                    raise XRPLError(
                        f"Wallet creation failed: {str(e)}",
                        details={"merchant_id": merchant_id}
                    )
    
    def get_wallet(
        self,
        merchant_id: str,
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Retrieve wallet information for a merchant.
        
        Args:
            merchant_id: Merchant identifier
            include_private: Whether to include private key
            
        Returns:
            Dict containing wallet information
            
        Raises:
            XRPLError: If wallet not found or access error
        """
        with error_context("get_wallet"):
            try:
                wallet_data = self._load_wallet(merchant_id)
                
                if not include_private:
                    wallet_data.pop("private_key", None)
                
                return wallet_data
                
            except Exception as e:
                logger.error(f"Failed to get wallet: {str(e)}", exc_info=True)
                raise XRPLError(
                    f"Wallet access failed: {str(e)}",
                    details={"merchant_id": merchant_id}
                )
    
    def _save_wallet(
        self,
        merchant_id: str,
        wallet_data: Dict[str, Any]
    ) -> None:
        """Encrypt and save wallet data."""
        wallet_path = self.storage_path / f"{merchant_id}.encrypted"
        
        # Encrypt wallet data
        encrypted_data = self.cipher_suite.encrypt(
            json.dumps(wallet_data).encode()
        )
        
        # Save to file
        with wallet_path.open('wb') as f:
            f.write(encrypted_data)
    
    def _load_wallet(self, merchant_id: str) -> Dict[str, Any]:
        """Load and decrypt wallet data."""
        wallet_path = self.storage_path / f"{merchant_id}.encrypted"
        
        if not wallet_path.exists():
            raise XRPLError(
                f"Wallet not found for merchant: {merchant_id}"
            )
        
        # Load and decrypt
        with wallet_path.open('rb') as f:
            encrypted_data = f.read()
            
        decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        return json.loads(decrypted_data) 