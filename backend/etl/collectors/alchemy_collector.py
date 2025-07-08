import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from web3 import Web3
from web3.exceptions import BlockNotFound
from web3.providers import HTTPProvider

from .base import BaseCollector

load_dotenv()


class AlchemyCollector(BaseCollector):
    """Collector for Ethereum blockchain data via Alchemy"""

    def __init__(self):
        super().__init__("alchemy")
        self.api_key = os.getenv("ALCHEMY_API_KEY")
        self.api_url = os.getenv("ALCHEMY_API_URL")

        # Set up connection pooling with retry strategy
        session = requests.Session()
        retry = Retry(
            total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Initialize Web3 with custom session
        self.w3 = Web3(
            HTTPProvider(
                f"{self.api_url}", request_kwargs={"timeout": 30}, session=session
            )
        )

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Alchemy")

        # Initialize Redis client for caching
        self.redis_client = redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
        )
        self.cache_ttl = 15  # seconds

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect current blockchain metrics with caching"""
        metrics = []

        # Check cache for recent block to avoid duplicate processing
        cached_block = self._get_cached_block()

        # Get latest block
        latest_block = self.w3.eth.get_block("latest")

        # Skip if we already processed this block
        if cached_block and cached_block == latest_block["number"]:
            self.logger.debug(
                f"Block {latest_block['number']} already processed, skipping"
            )
            return []

        # Cache the block number
        self._cache_block(latest_block["number"])

        # Get gas price
        gas_price = self.w3.eth.gas_price

        # Get pending transaction count
        try:
            pending_tx_count = self.w3.eth.get_block_transaction_count("pending")
        except BlockNotFound:
            self.logger.warning(
                "Pending block not found, using 0 for pending transaction count"
            )
            pending_tx_count = 0

        # Calculate base metrics
        block_metric = {
            "metric_type": "block",
            "timestamp": datetime.utcnow(),
            "block_number": latest_block["number"],
            "block_timestamp": datetime.fromtimestamp(latest_block["timestamp"]),
            "gas_used": latest_block["gasUsed"],
            "gas_limit": latest_block["gasLimit"],
            "transaction_count": len(latest_block["transactions"]),
            "base_fee_per_gas": latest_block.get("baseFeePerGas", 0),
            "difficulty": latest_block.get("difficulty", 0),
        }

        gas_metric = {
            "metric_type": "gas",
            "timestamp": datetime.utcnow(),
            "gas_price_wei": gas_price,
            "gas_price_gwei": float(Web3.from_wei(gas_price, "gwei")),
            "pending_transactions": pending_tx_count,
        }

        metrics.extend([block_metric, gas_metric])

        # Get mempool stats
        mempool_metric = await self._get_mempool_stats()
        if mempool_metric:
            metrics.append(mempool_metric)

        # Cache metrics for quick access
        self._cache_metrics(metrics)

        return metrics

    async def _get_mempool_stats(self) -> Optional[Dict[str, Any]]:
        """Get mempool statistics with caching"""
        try:
            # Check cache first
            cached_mempool = self._get_cached_mempool()
            if cached_mempool:
                return cached_mempool

            # Get pending transactions sample
            try:
                pending_block = self.w3.eth.get_block("pending", full_transactions=True)
            except BlockNotFound:
                self.logger.warning("Pending block not found for mempool stats")
                return None

            if pending_block and "transactions" in pending_block:
                transactions = pending_block["transactions"][:100]  # Sample first 100

                gas_prices = [tx["gasPrice"] for tx in transactions if "gasPrice" in tx]

                mempool_data = {
                    "metric_type": "mempool",
                    "timestamp": datetime.utcnow(),
                    "pending_count": len(pending_block["transactions"]),
                    "avg_gas_price_gwei": float(
                        Web3.from_wei(sum(gas_prices) / len(gas_prices), "gwei")
                    )
                    if gas_prices
                    else 0,
                    "min_gas_price_gwei": float(Web3.from_wei(min(gas_prices), "gwei"))
                    if gas_prices
                    else 0,
                    "max_gas_price_gwei": float(Web3.from_wei(max(gas_prices), "gwei"))
                    if gas_prices
                    else 0,
                }

                # Cache mempool data
                self._cache_mempool(mempool_data)

                return mempool_data
        except Exception as e:
            self.logger.error(f"Error getting mempool stats: {e}")
            return None

    def _get_cached_block(self) -> Optional[int]:
        """Get cached block number"""
        try:
            cached = self.redis_client.get("latest_block")
            return int(cached) if cached else None
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")
            return None

    def _cache_block(self, block_number: int):
        """Cache block number"""
        try:
            self.redis_client.setex("latest_block", self.cache_ttl, str(block_number))
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")

    def _get_cached_mempool(self) -> Optional[Dict[str, Any]]:
        """Get cached mempool data"""
        try:
            cached = self.redis_client.get("mempool_stats")
            return json.loads(cached) if cached else None
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")
            return None

    def _cache_mempool(self, data: Dict[str, Any]):
        """Cache mempool data"""
        try:
            # Convert datetime to string for JSON serialization
            data_copy = data.copy()
            data_copy["timestamp"] = data_copy["timestamp"].isoformat()
            self.redis_client.setex("mempool_stats", 5, json.dumps(data_copy))
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")

    def _cache_metrics(self, metrics: List[Dict[str, Any]]):
        """Cache latest metrics for quick access"""
        try:
            for metric in metrics:
                metric_copy = metric.copy()
                if isinstance(metric_copy.get("timestamp"), datetime):
                    metric_copy["timestamp"] = metric_copy["timestamp"].isoformat()
                if isinstance(metric_copy.get("block_timestamp"), datetime):
                    metric_copy["block_timestamp"] = metric_copy[
                        "block_timestamp"
                    ].isoformat()

                key = f"latest_{metric['metric_type']}"
                self.redis_client.setex(key, self.cache_ttl, json.dumps(metric_copy))
        except Exception as e:
            self.logger.warning(f"Redis cache error: {e}")
