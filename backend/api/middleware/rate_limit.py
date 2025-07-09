import time
from typing import Dict, Optional

import redis
from fastapi import HTTPException, Request


class RateLimiter:
    """Token bucket rate limiter with Redis backend"""

    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.limits = {
            "default": {"requests": 100, "window": 3600},  # 100 req/hour
            "metrics": {"requests": 1000, "window": 3600},  # 1000 req/hour
            "websocket": {"requests": 10, "window": 60},  # 10 connections/min
            "premium": {"requests": 10000, "window": 3600},  # Premium tier
        }

    async def check_rate_limit(
        self, request: Request, tier: str = "default", identifier: Optional[str] = None
    ) -> Dict[str, int]:
        """Check and update rate limit"""
        # Get identifier (API key or IP)
        if not identifier:
            identifier = request.client.host

        key = f"rate_limit:{tier}:{identifier}"
        limit_config = self.limits.get(tier, self.limits["default"])

        try:
            current = self.redis_client.incr(key)
            if current == 1:
                self.redis_client.expire(key, limit_config["window"])

            ttl = self.redis_client.ttl(key)
            remaining = max(0, limit_config["requests"] - current)

            if current > limit_config["requests"]:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": ttl,
                        "limit": limit_config["requests"],
                        "window": limit_config["window"],
                    },
                )

            return {
                "limit": limit_config["requests"],
                "remaining": remaining,
                "reset": int(time.time()) + ttl,
            }

        except redis.RedisError:
            # Fallback to allow requests if Redis is down
            return {
                "limit": limit_config["requests"],
                "remaining": limit_config["requests"],
                "reset": int(time.time()) + limit_config["window"],
            }
