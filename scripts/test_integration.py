import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from backend.etl.collectors.alchemy_collector import AlchemyCollector  # noqa: E402
from backend.models.database import engine  # noqa: E402
from backend.models.metrics import Base  # noqa: E402


async def test_integration():
    """Test full ETL pipeline integration"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    print("Testing Alchemy connection...")
    collector = AlchemyCollector()
    metrics = await collector.collect()

    print(f"Collected {len(metrics)} metrics:")
    for metric in metrics:
        print(f"  - {metric['metric_type']}: {metric.get('block_number', 'N/A')}")

    print("\nIntegration test completed successfully!")


if __name__ == "__main__":
    asyncio.run(test_integration())
