import os
from typing import Any

from fastapi import Depends, Request

from backend.api.middleware.auth import APIKeyAuth
from backend.api.middleware.rate_limit import RateLimiter

auth = APIKeyAuth()
rate_limiter = RateLimiter(os.getenv("REDIS_URL", "redis://localhost:6379"))


async def verify_request(
    request: Request, user_info: dict[str, Any] = Depends(auth.verify_api_key)
) -> dict[str, Any]:
    """Verify request with auth and rate limiting"""
    # Check rate limit based on user tier
    rate_limit_info = await rate_limiter.check_rate_limit(
        request, tier=user_info["tier"], identifier=user_info["name"]
    )

    # Add rate limit headers to response
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit": str(rate_limit_info["limit"]),
        "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
        "X-RateLimit-Reset": str(rate_limit_info["reset"]),
    }

    return user_info
