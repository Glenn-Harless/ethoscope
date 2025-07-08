import asyncio
import logging

from backend.etl.collectors.alchemy_collector import AlchemyCollector
from backend.etl.loaders.database_loader import DatabaseLoader
from backend.etl.processors.metric_processor import MetricProcessor

logger = logging.getLogger(__name__)


class ETLPipeline:
    """Main ETL pipeline orchestrator"""

    def __init__(self):
        self.collector = AlchemyCollector()
        self.processor = MetricProcessor()
        self.loader = DatabaseLoader()
        self.running = False

    async def run(self, interval: int = 15):
        """Run the ETL pipeline continuously"""
        self.running = True
        logger.info("Starting ETL pipeline")

        while self.running:
            try:
                # Collect data
                raw_data = await self.collector.collect()
                logger.info(f"Collected {len(raw_data)} raw metrics")

                # Process data
                processed_data = await self.processor.process(raw_data)
                logger.info(f"Processed {len(processed_data)} metrics")

                # Load data
                await self.loader.load(processed_data)
                logger.info("Data loaded successfully")

                # Wait for next cycle
                await asyncio.sleep(interval)

            except Exception as e:
                logger.error(f"Pipeline error: {e}", exc_info=True)
                await asyncio.sleep(interval)

    async def stop(self):
        """Stop the pipeline"""
        self.running = False
        logger.info("Stopping ETL pipeline")
