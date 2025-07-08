import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.etl.pipeline import ETLPipeline  # noqa: E402

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def main():
    """Run the ETL pipeline"""
    pipeline = ETLPipeline()

    try:
        await pipeline.run()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
        await pipeline.stop()


if __name__ == "__main__":
    asyncio.run(main())
