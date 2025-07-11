import asyncio
import sys
from pathlib import Path

# Add parent directory to path before imports
sys.path.append(str(Path(__file__).parent.parent))

from backend.etl.collectors.flashbots_collector import FlashbotsCollector
from backend.etl.collectors.l2_collector import L2Collector


async def test_collectors():
    """Test new collectors"""
    print("Testing Flashbots Collector...")
    flashbots = FlashbotsCollector()
    flashbots_data = await flashbots.collect()
    print(f"Collected {len(flashbots_data)} Flashbots metrics")

    print("\nTesting L2 Collector...")
    l2 = L2Collector()
    l2_data = await l2.collect()
    print(f"Collected {len(l2_data)} L2 metrics")

    # Cleanup
    await flashbots.close()
    await l2.close()


if __name__ == "__main__":
    asyncio.run(test_collectors())
