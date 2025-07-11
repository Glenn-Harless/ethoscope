import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for all data collectors"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def collect(self) -> list[dict[str, Any]]:
        """Collect data from source"""

    async def run_collection(self, interval: int = 60):
        """Run collection continuously at specified interval"""
        while True:
            try:
                data = await self.collect()
                self.logger.info(f"Collected {len(data)} items")
                yield data
            except Exception as e:
                self.logger.error(f"Collection error: {e}")
            await asyncio.sleep(interval)
