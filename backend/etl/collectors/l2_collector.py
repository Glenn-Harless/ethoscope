import asyncio
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from web3 import Web3

from .base import BaseCollector


class L2Collector(BaseCollector):
    """Collector for L2 network metrics"""

    def __init__(self):
        super().__init__("l2_networks")

        # Initialize L2 connections with expanded network support
        alchemy_key = os.getenv("ALCHEMY_API_KEY")
        self.networks = {
            "arbitrum": {
                "rpc": f"https://arb-mainnet.g.alchemy.com/v2/{alchemy_key}",
                "chain_id": 42161,
                "name": "Arbitrum One",
                "type": "optimistic_rollup",
            },
            "optimism": {
                "rpc": f"https://opt-mainnet.g.alchemy.com/v2/{alchemy_key}",
                "chain_id": 10,
                "name": "Optimism",
                "type": "optimistic_rollup",
            },
            "polygon": {
                "rpc": f"https://polygon-mainnet.g.alchemy.com/v2/{alchemy_key}",
                "chain_id": 137,
                "name": "Polygon PoS",
                "type": "sidechain",
            },
            "base": {
                "rpc": f"https://base-mainnet.g.alchemy.com/v2/{alchemy_key}",
                "chain_id": 8453,
                "name": "Base",
                "type": "optimistic_rollup",
            },
            "zksync": {
                "rpc": "https://mainnet.era.zksync.io",
                "chain_id": 324,
                "name": "zkSync Era",
                "type": "zk_rollup",
            },
            "scroll": {
                "rpc": "https://rpc.scroll.io",
                "chain_id": 534352,
                "name": "Scroll",
                "type": "zk_rollup",
            },
        }

        # Initialize Web3 connections
        self.w3_connections = {}
        for network, config in self.networks.items():
            self.w3_connections[network] = Web3(Web3.HTTPProvider(config["rpc"]))

        # L2Beat API for additional metrics
        self.l2beat_client = httpx.AsyncClient(timeout=30.0)

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect metrics from all L2 networks"""
        metrics = []

        # Collect from each L2 network
        tasks = []
        for network in self.networks:
            tasks.append(self._collect_network_metrics(network))

        network_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in network_results:
            if isinstance(result, list):
                metrics.extend(result)
            elif isinstance(result, Exception):
                self.logger.error(f"L2 collection error: {result}")

        # Get L2Beat TVL data
        l2beat_data = await self._get_l2beat_data()
        if l2beat_data:
            metrics.extend(l2beat_data)

        return metrics

    async def _collect_network_metrics(self, network: str) -> List[Dict[str, Any]]:
        """Collect metrics from specific L2 network"""
        try:
            w3 = self.w3_connections[network]

            if not w3.is_connected():
                self.logger.warning(f"{network} not connected")
                return []

            # Get latest block
            latest_block = w3.eth.get_block("latest")

            # Get gas price
            gas_price = w3.eth.gas_price

            # Get L1 gas price for comparison (from oracle if available)
            l1_gas_price = await self._get_l1_gas_price(network)

            metrics = []

            # Basic L2 metrics
            l2_metric = {
                "metric_type": "l2_network",
                "timestamp": datetime.utcnow(),
                "network": network,
                "chain_id": self.networks[network]["chain_id"],
                "block_number": latest_block["number"],
                "gas_price_wei": gas_price,
                "gas_price_gwei": float(Web3.from_wei(gas_price, "gwei")),
                "transaction_count": len(latest_block["transactions"]),
                "block_time": latest_block["timestamp"],
            }

            # L1 vs L2 comparison
            if l1_gas_price:
                l2_metric["l1_gas_price_gwei"] = l1_gas_price
                l2_metric["gas_savings_percent"] = (
                    (l1_gas_price - l2_metric["gas_price_gwei"]) / l1_gas_price
                ) * 100

            # Add rollup-specific metrics
            if self.networks[network]["type"] in ["optimistic_rollup", "zk_rollup"]:
                rollup_metrics = await self._get_rollup_specific_metrics(network, w3)
                l2_metric.update(rollup_metrics)

            metrics.append(l2_metric)

            # Get transaction costs comparison
            cost_comparison = await self._calculate_transaction_costs(
                network, gas_price
            )
            if cost_comparison:
                metrics.append(cost_comparison)

            # Get sequencer health metrics
            if self.networks[network]["type"] in ["optimistic_rollup", "zk_rollup"]:
                sequencer_health = await self._check_sequencer_health(network)
                if sequencer_health:
                    metrics.append(sequencer_health)

            return metrics

        except Exception as e:
            self.logger.error(f"Error collecting {network} metrics: {e}")
            return []

    async def _get_l1_gas_price(self, network: str) -> Optional[float]:
        """Get L1 gas price from L2 oracle contracts"""
        try:
            # This would query specific oracle contracts on each L2
            # For now, return cached L1 gas price from Redis
            redis_client = self._get_redis_client()
            l1_gas = redis_client.get("latest_gas")
            if l1_gas:
                import json

                gas_data = json.loads(l1_gas)
                return gas_data.get("gas_price_gwei", 0)
            return None
        except Exception as e:
            self.logger.error(f"Error getting L1 gas price: {e}")
            return None

    async def _calculate_transaction_costs(
        self, network: str, gas_price: int
    ) -> Optional[Dict[str, Any]]:
        """Calculate transaction costs for common operations"""
        try:
            # Gas estimates for common operations
            operations = {
                "eth_transfer": 21000,
                "erc20_transfer": 65000,
                "uniswap_swap": 150000,
                "nft_mint": 100000,
            }

            costs = {}
            for op, gas_limit in operations.items():
                cost_wei = gas_price * gas_limit
                cost_eth = Web3.from_wei(cost_wei, "ether")
                cost_usd = float(cost_eth) * await self._get_eth_price()
                costs[f"{op}_cost_usd"] = cost_usd

            return {
                "metric_type": "l2_transaction_costs",
                "timestamp": datetime.utcnow(),
                "network": network,
                **costs,
            }

        except Exception as e:
            self.logger.error(f"Error calculating transaction costs: {e}")
            return None

    async def _get_l2beat_data(self) -> List[Dict[str, Any]]:
        """Get TVL and activity data from L2Beat"""
        try:
            response = await self.l2beat_client.get("https://l2beat.com/api/tvl")
            response.raise_for_status()
            data = response.json()

            metrics = []
            for project in data.get("projects", []):
                if project["name"].lower() in self.networks:
                    metrics.append(
                        {
                            "metric_type": "l2_tvl",
                            "timestamp": datetime.utcnow(),
                            "network": project["name"].lower(),
                            "tvl_usd": project.get("tvl", {}).get("usd", 0),
                            "tvl_eth": project.get("tvl", {}).get("eth", 0),
                            "daily_tps": project.get("tps", 0),
                            "market_share_percent": project.get("marketShare", 0),
                        }
                    )

            return metrics

        except Exception as e:
            self.logger.error(f"Error getting L2Beat data: {e}")
            return []

    async def _get_rollup_specific_metrics(
        self, network: str, w3: Web3
    ) -> Dict[str, Any]:
        """Get rollup-specific metrics like L1 data costs and state commitments"""
        metrics = {}

        try:
            if network in ["arbitrum", "optimism", "base"]:
                # Optimistic rollup metrics
                metrics["l1_data_submission_cost"] = await self._get_l1_data_cost(
                    network
                )
                metrics["challenge_period_hours"] = (
                    168 if network == "arbitrum" else 7 * 24
                )
                metrics["state_root_frequency"] = "hourly"
            elif network in ["zksync", "scroll"]:
                # ZK rollup metrics
                metrics[
                    "proof_generation_time"
                ] = await self._get_proof_generation_time(network)
                metrics["l1_verification_cost"] = await self._get_verification_cost(
                    network
                )
                metrics["batch_size"] = await self._get_average_batch_size(network)

            # Common rollup metrics
            metrics["l1_submission_frequency"] = await self._get_submission_frequency(
                network
            )
            metrics["data_availability_cost"] = await self._get_da_cost(network)

        except Exception as e:
            self.logger.error(f"Error getting rollup metrics for {network}: {e}")

        return metrics

    async def _check_sequencer_health(self, network: str) -> Optional[Dict[str, Any]]:
        """Check sequencer health and decentralization metrics"""
        try:
            health_endpoints = {
                "arbitrum": "https://arb1.arbitrum.io/rpc",
                "optimism": "https://mainnet.optimism.io",
                "base": "https://mainnet.base.org",
                "zksync": "https://mainnet.era.zksync.io",
                "scroll": "https://rpc.scroll.io",
            }

            # Check sequencer uptime
            start_time = time.time()
            response = await self.client.post(
                health_endpoints.get(network, ""),
                json={
                    "jsonrpc": "2.0",
                    "method": "eth_blockNumber",
                    "params": [],
                    "id": 1,
                },
            )
            latency = (time.time() - start_time) * 1000  # ms

            return {
                "metric_type": "sequencer_health",
                "timestamp": datetime.utcnow(),
                "network": network,
                "sequencer_latency_ms": latency,
                "sequencer_uptime": response.status_code == 200,
                "decentralization_score": await self._calculate_decentralization_score(
                    network
                ),
            }

        except Exception as e:
            self.logger.error(f"Error checking sequencer health: {e}")
            return None

    async def _get_eth_price(self) -> float:
        """Get current ETH price in USD"""
        try:
            # In production, this would query a price oracle
            # For now, return a static value
            return 2000.0
        except Exception:
            return 2000.0

    def _get_redis_client(self):
        """Get Redis client for caching"""
        import redis

        return redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
        )

    async def close(self):
        """Close connections"""
        await self.l2beat_client.aclose()
