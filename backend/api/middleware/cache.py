import hashlib
import json
from collections.abc import Callable

from redis import Redis


class MetricsCache:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.default_ttl = 30  # seconds

    async def get_or_compute(self, key: str, compute_func: Callable, ttl: int = None):
        """Get from cache or compute and store"""
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)

        result = await compute_func()
        self.redis.setex(key, ttl or self.default_ttl, json.dumps(result))
        return result

    def cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        params = json.dumps(kwargs, sort_keys=True)
        return f"{prefix}:{hashlib.md5(params.encode()).hexdigest()}"
