"""
XRPL payment monitoring service.

This module handles monitoring of XRPL transactions and processes
incoming payments for merchants.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import threading
from queue import Queue
import time

from xrpl.clients import JsonRpcClient
from xrpl.models.requests import AccountTx
from xrpl.models.response import Response

from core.exceptions import XRPLError, DatabaseError
from core.error_handlers import with_retry, error_context
from core.metrics import metrics_collector
from core.monitoring import AlertManager

logger = logging.getLogger(__name__)

class PaymentMonitor:
    """Service for monitoring XRPL payments."""
    
    def __init__(
        self,
        merchant_address: str,
        alert_manager: AlertManager,
        max_queue_size: int = 1000
    ):
        self.merchant_address = merchant_address
        self.alert_manager = alert_manager
        self.client = JsonRpcClient("wss://s.altnet.rippletest.net:51233")
        self.transaction_queue: Queue = Queue(maxsize=max_queue_size)
        self.shutdown_event = threading.Event()
        
        # Initialize metrics
        self.metrics = metrics_collector
        
    def start(self) -> None:
        """Start the payment monitoring service."""
        logger.info(f"Starting payment monitor for {self.merchant_address}")
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_transactions,
            daemon=True
        )
        self.processing_thread.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitor_payments,
            daemon=True
        )
        self.monitoring_thread.start()
    
    @with_retry(max_attempts=3, exceptions=(XRPLError,))
    def _fetch_transactions(self) -> Response:
        """Fetch transactions from XRPL."""
        with error_context("fetch_transactions"):
            with metrics_collector.measure_latency('xrpl_request'):
                return self.client.request(
                    AccountTx(account=self.merchant_address)
                )
    
    def _monitor_payments(self) -> None:
        """Monitor XRPL for new payments."""
        while not self.shutdown_event.is_set():
            try:
                response = self._fetch_transactions()
                
                for tx in response.result.get('transactions', []):
                    if self._is_valid_payment(tx):
                        self.transaction_queue.put(tx)
                        
                time.sleep(1)  # Avoid overwhelming the node
                
            except Exception as e:
                logger.error("Error monitoring payments", exc_info=True)
                self.alert_manager.send_alert(
                    "payment_monitor_error",
                    {"error": str(e)}
                )
                time.sleep(5)  # Back off on error
    
    def _process_transactions(self) -> None:
        """Process queued transactions."""
        while not self.shutdown_event.is_set():
            try:
                tx = self.transaction_queue.get(timeout=1)
                self._process_transaction(tx)
                self.transaction_queue.task_done()
                
            except Queue.Empty:
                continue
            except Exception as e:
                logger.error("Error processing transaction", exc_info=True)
                self.alert_manager.send_alert(
                    "transaction_processing_error",
                    {"error": str(e)}
                )
    
    def _process_transaction(self, transaction: Dict[str, Any]) -> None:
        """Process a single transaction."""
        with error_context("process_transaction"):
            with metrics_collector.measure_latency('transaction_processing'):
                # Process payment logic here
                pass
    
    def _is_valid_payment(self, transaction: Dict[str, Any]) -> bool:
        """Validate if transaction is a valid payment."""
        return (
            transaction.get('TransactionType') == 'Payment'
            and transaction.get('Destination') == self.merchant_address
        )
    
    def stop(self) -> None:
        """Stop the payment monitoring service."""
        logger.info("Stopping payment monitor")
        self.shutdown_event.set()
        self.monitoring_thread.join()
        self.processing_thread.join() 