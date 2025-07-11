import asyncio
import logging
from typing import Any

from backend.api.websocket import WebSocketManager
from backend.etl.collectors.alchemy_collector import AlchemyCollector
from backend.etl.collectors.flashbots_collector import FlashbotsCollector
from backend.etl.collectors.l2_collector import L2Collector
from backend.etl.loaders.database_loader import DatabaseLoader
from backend.etl.processors.health_score_calculator import (
    DynamicNetworkHealthCalculator as NetworkHealthCalculator,
)
from backend.etl.processors.metric_processor import MetricProcessor
from backend.models.database import SessionLocal

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Enhanced ETL pipeline orchestrator with multiple collectors"""

    def __init__(self, ws_manager: WebSocketManager = None):
        self.collectors = {
            "alchemy": AlchemyCollector(),
            "flashbots": FlashbotsCollector(),
            "l2": L2Collector(),
        }
        self.processor = MetricProcessor()
        self.loader = DatabaseLoader()
        self.health_calculator = NetworkHealthCalculator()
        self.ws_manager = ws_manager
        self.running = False

    async def run(self, interval: int = 15):
        """Run the enhanced ETL pipeline"""
        self.running = True
        logger.info("Starting enhanced ETL pipeline with multiple collectors")

        while self.running:
            try:
                # Collect data from all sources concurrently
                collect_tasks = [collector.collect() for collector in self.collectors.values()]

                all_metrics = await asyncio.gather(*collect_tasks, return_exceptions=True)

                # Flatten results and handle errors
                raw_data = []
                for result in all_metrics:
                    if isinstance(result, list):
                        raw_data.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"Collection error: {result}")

                logger.info(f"Collected {len(raw_data)} raw metrics from all sources")

                # Process data
                processed_data = await self.processor.process(raw_data)
                logger.info(
                    "Processed metrics: "
                    + ", ".join(f"{k}: {len(v)}" for k, v in processed_data.items() if v)
                )

                # Calculate network health score
                db = SessionLocal()
                try:
                    health_score = await self.health_calculator.calculate_health_score(db)
                    processed_data["network_health_scores"] = [health_score]
                finally:
                    db.close()

                # Load data
                await self.loader.load(processed_data)
                logger.info("Data loaded successfully")

                # Send real-time updates via WebSocket
                if self.ws_manager:
                    await self._send_realtime_updates(processed_data)

                # Wait for next cycle
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def _send_realtime_updates(self, processed_data: dict[str, list[dict[str, Any]]]):
        """Send real-time updates through WebSocket"""
        try:
            # Send gas price updates
            if processed_data.get("gas_metrics"):
                latest_gas = processed_data["gas_metrics"][-1]
                await self.ws_manager.send_metric_update("gas_prices", latest_gas)

            # Send network health updates
            if processed_data.get("network_health_scores"):
                latest_health = processed_data["network_health_scores"][-1]
                await self.ws_manager.send_metric_update("network_health", latest_health)

            # Send MEV activity updates
            if processed_data.get("mev_metrics"):
                latest_mev = processed_data["mev_metrics"][-1]
                await self.ws_manager.send_metric_update("mev_activity", latest_mev)

            # Send L2 comparison updates
            if processed_data.get("l2_network_metrics"):
                l2_data = {
                    metric["network"]: metric for metric in processed_data["l2_network_metrics"]
                }
                await self.ws_manager.send_metric_update("l2_comparison", l2_data)

        except Exception as e:
            logger.error(f"Error sending WebSocket updates: {e}")

    async def stop(self):
        """Stop the pipeline and cleanup"""
        self.running = False
        logger.info("Stopping ETL pipeline")

        # Close collector connections
        for name, collector in self.collectors.items():
            if hasattr(collector, "close"):
                await collector.close()
                logger.info(f"Closed {name} collector")
