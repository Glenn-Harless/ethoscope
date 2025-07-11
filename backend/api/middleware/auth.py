import os
from datetime import datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security = HTTPBearer()


class APIKeyAuth:
    """API Key authentication with tier support"""

    def __init__(self):
        self.secret_key = os.getenv("API_SECRET_KEY", "your-secret-key")
        self.api_keys = {}  # In production, use database

        # Sample API keys with tiers
        self._init_sample_keys()

    def _init_sample_keys(self):
        """Initialize sample API keys (use database in production)"""
        self.api_keys = {
            "demo-key-123": {
                "tier": "default",
                "name": "Demo User",
                "created": datetime.utcnow(),
                "permissions": ["read"],
            },
            "premium-key-456": {
                "tier": "premium",
                "name": "Premium User",
                "created": datetime.utcnow(),
                "permissions": ["read", "write", "stream"],
            },
        }

    async def verify_api_key(
        self, credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> dict[str, Any]:
        """Verify API key and return user info"""
        api_key = credentials.credentials

        if api_key not in self.api_keys:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return self.api_keys[api_key]

    def create_jwt_token(self, user_info: dict[str, Any], expires_delta: timedelta = None) -> str:
        """Create JWT token for WebSocket auth"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)

        payload = {
            "sub": user_info["name"],
            "tier": user_info["tier"],
            "permissions": user_info["permissions"],
            "exp": expire,
        }

        return jwt.encode(payload, self.secret_key, algorithm="HS256")
