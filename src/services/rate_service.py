"""
Exchange rate service for fleXRP.

This module handles fetching and caching of exchange rates
for XRP to fiat currency conversion.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading
import requests
from cachetools import TTLCache

from core.exceptions import APIError
from core.error_handlers import with_retry, error_context
from core.metrics import metrics_collector

logger = logging.getLogger(__name__)

class RateService:
    """Service for managing exchange rates."""
    
    def __init__(
        self,
        api_key: str,
        cache_ttl: int = 300,  # 5 minutes
        update_interval: int = 60  # 1 minute
    ):
        self.api_key = api_key
        self.base_url = "https://pro-api.coinmarketcap.com/v1"
        self.cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.update_interval = update_interval
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
        # Initialize metrics
        self.metrics = metrics_collector
        
        # Start background updater
        self.update_thread = threading.Thread(
            target=self._update_rates,
            daemon=True
        )
        self.update_thread.start()
    
    @with_retry(max_attempts=3, exceptions=(APIError,))
    def get_rate(
        self,
        fiat_currency: str = "USD"
    ) -> float:
        """
        Get current XRP to fiat exchange rate.
        
        Args:
            fiat_currency: Target fiat currency code
            
        Returns:
            Current exchange rate
            
        Raises:
            APIError: If rate fetch fails
        """
        with error_context("get_rate"):
            with self.lock:
                cache_key = f"XRP_{fiat_currency}"
                
                if cache_key in self.cache:
                    return self.cache[cache_key]
                
                rate = self._fetch_rate(fiat_currency)
                self.cache[cache_key] = rate
                return rate
    
    def _fetch_rate(self, fiat_currency: str) -> float:
        """Fetch current rate from API."""
        with metrics_collector.measure_latency('rate_api_request'):
            try:
                response = requests.get(
                    f"{self.base_url}/cryptocurrency/quotes/latest",
                    params={
                        "symbol": "XRP",
                        "convert": fiat_currency
                    },
                    headers={
                        "X-CMC_PRO_API_KEY": self.api_key,
                        "Accept": "application/json"
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                return float(
                    data["data"]["XRP"]["quote"][fiat_currency]["price"]
                )
                
            except Exception as e:
                logger.error(f"Failed to fetch rate: {str(e)}", exc_info=True)
                raise APIError(
                    f"Rate fetch failed: {str(e)}",
                    details={"currency": fiat_currency}
                )
    
    def _update_rates(self) -> None:
        """Background task to update rates."""
        while not self.shutdown_event.is_set():
            try:
                self.get_rate("USD") 