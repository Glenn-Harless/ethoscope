import logging
from asyncio import Semaphore
from datetime import datetime
from typing import Any, Optional

import backoff
import httpx
from cachetools import TTLCache

from backend.utils.circuit_breaker import circuit_breaker

from .base import BaseCollector

logger = logging.getLogger(__name__)


class FlashbotsCollector(BaseCollector):
    """Enhanced collector for comprehensive MEV data using current APIs"""

    def __init__(self):
        super().__init__("flashbots")
        # Note: blocks.flashbots.net has been decommissioned
        # Now using MEV-Boost relay APIs for data
        self.relay_urls = {
            "flashbots": "https://boost-relay.flashbots.net",
            # "ultra_sound": "https://relay.ultrasound.money",
            "bloxroute_max": "https://bloxroute.max-profit.blxrbdn.com",
            # "bloxroute_ethical": "https://bloxroute.ethical.blxrbdn.com",
            # "blocknative": "https://builder-relay-mainnet.blocknative.com",
            # "manifold": "https://mainnet-relay.securerpc.com",
            "agnostic": "https://agnostic-relay.net",
        }
        self.client = httpx.AsyncClient(timeout=30.0)
        self.dex_addresses = {
            "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
            "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
            "balancer": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        }
        self.connection_pool = Semaphore(10)  # Limit concurrent connections
        self.request_cache = TTLCache(maxsize=1000, ttl=60)

    async def collect(self) -> list[dict[str, Any]]:
        """Collect MEV metrics from relay APIs"""
        metrics = []

        try:
            # Get recent MEV blocks from all relays
            relay_blocks = await self._get_relay_blocks()

            # Process blocks for MEV patterns
            for block in relay_blocks[:50]:  # Process last 50 blocks
                mev_metric = await self._process_relay_block(block)
                if mev_metric:
                    metrics.append(mev_metric)

                # Analyze block MEV characteristics
                mev_analysis = await self._analyze_block_mev_characteristics(block)
                metrics.append(
                    {
                        "metric_type": "mev_block_analysis",
                        "timestamp": datetime.utcnow(),
                        **mev_analysis,
                    }
                )

            # Get aggregated MEV-Boost stats
            boost_stats = await self._get_mev_boost_stats()
            if boost_stats:
                metrics.append(boost_stats)

        except Exception as e:
            self.logger.error(f"MEV collection error: {e}")

        return metrics

    async def _get_relay_blocks(self) -> list[dict[str, Any]]:
        """Get recent blocks from MEV-Boost relays"""
        all_blocks = []

        for relay_name, relay_url in self.relay_urls.items():
            try:
                # Use the proposer_payload_delivered endpoint
                endpoint = f"{relay_url}/relay/v1/data/bidtraces/proposer_payload_delivered"
                response = await self.client.get(
                    endpoint,
                    params={"limit": 100},  # Get last 100 blocks per relay
                )

                if response.status_code == 200:
                    blocks = response.json()
                    # Tag each block with its relay source
                    for block in blocks:
                        block["relay_source"] = relay_name
                    all_blocks.extend(blocks)

            except Exception as e:
                self.logger.error(f"Error fetching from {relay_name}: {e}")

        # Sort by slot/block number
        all_blocks.sort(key=lambda x: int(x.get("block_number", 0)), reverse=True)
        return all_blocks

    async def _process_relay_block(self, block: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Process relay block data for MEV metrics"""
        try:
            # Extract data from MEV-Boost relay response format
            block_number = int(block.get("block_number", 0))
            slot = int(block.get("slot", 0))
            value_wei = int(block.get("value", 0))

            # Convert builder and proposer pubkeys to addresses
            builder_pubkey = block.get("builder_pubkey", "")
            proposer_fee_recipient = block.get("proposer_fee_recipient", "")

            # Calculate MEV metrics from relay data
            mev_value_eth = value_wei / 1e18
            gas_used = int(block.get("gas_used", 0))
            gas_limit = int(block.get("gas_limit", 0))

            return {
                "metric_type": "mev",
                "timestamp": datetime.utcnow(),
                "block_number": block_number,
                "slot": slot,
                "total_mev_revenue": mev_value_eth,
                "builder_pubkey": builder_pubkey,
                "proposer_fee_recipient": proposer_fee_recipient,
                "gas_used": gas_used,
                "gas_limit": gas_limit,
                "gas_utilization": (gas_used / gas_limit * 100) if gas_limit > 0 else 0,
                "relay_source": block.get("relay_source", "unknown"),
                "block_hash": block.get("block_hash", ""),
                "parent_hash": block.get("parent_hash", ""),
            }

        except Exception as e:
            self.logger.error(f"Error processing Flashbots block: {e}")
            return None

    async def _analyze_block_mev_characteristics(self, block: dict[str, Any]) -> dict[str, Any]:
        """Analyze MEV characteristics from block-level data"""
        value_eth = int(block.get("value", 0)) / 1e18
        gas_used = int(block.get("gas_used", 0))
        gas_limit = int(block.get("gas_limit", 1))

        return {
            "mev_intensity": ("high" if value_eth > 5 else "medium" if value_eth > 1 else "low"),
            "value_eth": value_eth,
            "gas_efficiency": gas_used / gas_limit if gas_limit > 0 else 0,
            "builder": block.get("builder_pubkey", ""),
            "likely_mev_type": self._estimate_mev_type_from_value(value_eth),
            "relay_source": block.get("relay_source", ""),
            "block_number": int(block.get("block_number", 0)),
            "slot": int(block.get("slot", 0)),
        }

    def _estimate_mev_type_from_value(self, value_eth: float) -> str:
        """Rough heuristic for MEV type based on block value"""
        if value_eth > 10:
            return "likely_contains_liquidations"
        elif value_eth > 3:
            return "likely_high_value_arbitrage"
        elif value_eth > 0.5:
            return "likely_standard_mev"
        else:
            return "minimal_mev"

    # The following methods would require transaction data which isn't
    # available from relay APIs. They're kept here as documentation for
    # future implementation with additional data sources

    def _get_mev_analysis_options(self) -> dict[str, str]:
        """Document options for implementing MEV analysis"""
        return {
            "option_1": "Connect to Ethereum node for full block data",
            "option_2": "Use MEV-Inspect-Py library for analysis",
            "option_3": "Query Dune Analytics API for pre-processed MEV data",
            "option_4": "Use Flashbots Bundle API for bundle simulation",
            "current_limitation": (
                "Relay APIs only provide block-level MEV revenue, " "not transaction details"
            ),
        }

    async def _get_builder_dominance(self) -> dict[str, float]:
        """Calculate builder market share"""
        # Get latest slot from the most recent block
        latest_blocks = await self._get_relay_blocks()
        if not latest_blocks:
            return {}

        end_slot = int(latest_blocks[0].get("slot", 0))
        start_slot = end_slot - 7200  # Last 24 hours (approximately)

        builder_blocks = {}
        total_blocks = 0

        for relay_name, relay_url in self.relay_urls.items():
            try:
                response = await self.client.get(
                    f"{relay_url}/relay/v1/data/bidtraces/proposer_payload_delivered",
                    params={"slot_gte": start_slot, "slot_lte": end_slot},
                )
                if response.status_code == 200:
                    blocks = response.json()
                    for block in blocks:
                        builder = block.get("builder_pubkey", "unknown")
                        builder_blocks[builder] = builder_blocks.get(builder, 0) + 1
                        total_blocks += 1
            except Exception as e:
                self.logger.error(f"Error fetching from {relay_name}: {e}")

        # Calculate market share
        market_share = {
            builder: (count / total_blocks) * 100 for builder, count in builder_blocks.items()
        }

        return market_share

    async def _analyze_private_mempool_usage(self) -> dict[str, Any]:
        """Analyze private mempool and order flow auction usage"""
        # This would integrate with MEV-Share API and other private pools
        private_metrics = {
            "mev_share_volume": 0,
            "private_pool_percentage": 0,
            "exclusive_orderflow_value": 0,
        }

        # Check MEV-Share submissions
        try:
            # MEV-Share API integration would go here
            pass
        except Exception as e:
            self.logger.error(f"Error analyzing private mempools: {e}")

        return private_metrics

    async def _get_mev_boost_stats(self) -> Optional[dict[str, Any]]:
        """Get MEV-Boost aggregate statistics"""
        try:
            # Aggregate data from all relays collected
            all_relay_blocks = await self._get_relay_blocks()

            if not all_relay_blocks:
                return None

            # Take last 100 blocks for statistics
            recent_blocks = all_relay_blocks[:100]

            if not recent_blocks:
                return None

            # Calculate statistics
            total_value = sum(float(b.get("value", 0)) for b in recent_blocks)
            avg_value = total_value / len(recent_blocks) if recent_blocks else 0

            return {
                "metric_type": "mev_boost_stats",
                "timestamp": datetime.utcnow(),
                "total_mev_revenue_eth": total_value / 1e18,
                "average_block_value_eth": avg_value / 1e18,
                "block_count": len(recent_blocks),
                "top_builder": self._get_top_builder(recent_blocks),
            }

        except Exception as e:
            self.logger.error(f"Error getting MEV-Boost stats: {e}")
            return None

    def _get_top_builder(self, blocks: list[dict]) -> str:
        """Identify top builder by block count"""
        builder_counts = {}
        for block in blocks:
            builder = block.get("builder_pubkey", "unknown")
            builder_counts[builder] = builder_counts.get(builder, 0) + 1

        return max(builder_counts, key=builder_counts.get) if builder_counts else "unknown"

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

    @circuit_breaker(failure_threshold=5, recovery_timeout=60)
    @backoff.on_exception(backoff.expo, httpx.HTTPError, max_tries=3)
    async def _get_flashbots_blocks(self) -> list[dict[str, Any]]:
        """Get Flashbots blocks with retry and circuit breaker"""
        async with self.connection_pool:
            # Check cache first
            cache_key = "flashbots_blocks_latest"
            if cache_key in self.request_cache:
                return self.request_cache[cache_key]

            try:
                # Note: This method is deprecated as blocks.flashbots.net
                # is decommissioned. Using relay API instead
                endpoint = (
                    f"{self.relay_urls['flashbots']}/relay/v1/data/"
                    "bidtraces/proposer_payload_delivered"
                )
                response = await self.client.get(endpoint, timeout=httpx.Timeout(10.0))
                response.raise_for_status()
                blocks = response.json().get("blocks", [])

                # Cache successful response
                self.request_cache[cache_key] = blocks
                return blocks

            except httpx.TimeoutException:
                logger.error("Flashbots API timeout")
                # Return cached data if available
                return self.request_cache.get(cache_key, [])
