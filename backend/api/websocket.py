import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Set

import redis.asyncio as redis
from fastapi import WebSocket

from backend.etl.config import settings

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        self.redis_client = None
        self.pubsub = None
        self.background_task = None

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()

        # Initialize Redis connection if not exists
        if not self.redis_client:
            self.redis_client = await redis.from_url(settings.redis_url)
            self.pubsub = self.redis_client.pubsub()

            # Start background task for Redis subscriptions
            if not self.background_task:
                self.background_task = asyncio.create_task(self._redis_listener())

        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        logger.info(f"WebSocket connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected: {websocket.client}")

    async def handle_message(self, websocket: WebSocket, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            action = data.get("action")

            if action == "subscribe":
                channels = data.get("channels", [])
                await self._subscribe(websocket, channels)
            elif action == "unsubscribe":
                channels = data.get("channels", [])
                await self._unsubscribe(websocket, channels)
            elif action == "ping":
                await websocket.send_json(
                    {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                )

        except json.JSONDecodeError:
            await websocket.send_json({"type": "error", "message": "Invalid JSON"})
        except Exception as e:
            logger.error(f"WebSocket message handling error: {e}")
            await websocket.send_json({"type": "error", "message": str(e)})

    async def _subscribe(self, websocket: WebSocket, channels: List[str]):
        """Subscribe to channels"""
        valid_channels = {
            "gas_prices",
            "block_metrics",
            "network_health",
            "mev_activity",
            "l2_comparison",
            "mempool_stats",
        }

        for channel in channels:
            if channel in valid_channels:
                self.subscriptions[websocket].add(channel)

                # Subscribe to Redis channel
                await self.pubsub.subscribe(f"metric:{channel}")

        await websocket.send_json(
            {"type": "subscribed", "channels": list(self.subscriptions[websocket])}
        )

    async def _unsubscribe(self, websocket: WebSocket, channels: List[str]):
        """Unsubscribe from channels"""
        for channel in channels:
            if channel in self.subscriptions[websocket]:
                self.subscriptions[websocket].remove(channel)

                # Check if any connection still needs this channel
                still_needed = any(
                    channel in subs
                    for ws, subs in self.subscriptions.items()
                    if ws != websocket
                )

                if not still_needed:
                    await self.pubsub.unsubscribe(f"metric:{channel}")

        await websocket.send_json(
            {"type": "unsubscribed", "channels": list(self.subscriptions[websocket])}
        )

    async def broadcast(self, channel: str, data: Dict):
        """Broadcast data to subscribed connections"""
        # Publish to Redis for multi-instance support
        if self.redis_client:
            await self.redis_client.publish(f"metric:{channel}", json.dumps(data))

    async def _redis_listener(self):
        """Listen for Redis pub/sub messages"""
        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode()
                    metric_type = channel.split(":")[-1]
                    data = json.loads(message["data"])

                    # Send to subscribed WebSocket connections
                    disconnected = []
                    for websocket, channels in self.subscriptions.items():
                        if metric_type in channels:
                            try:
                                await websocket.send_json(
                                    {
                                        "type": "update",
                                        "channel": metric_type,
                                        "data": data,
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                )
                            except Exception:
                                disconnected.append(websocket)

                    # Clean up disconnected clients
                    for ws in disconnected:
                        self.disconnect(ws)

        except Exception as e:
            logger.error(f"Redis listener error: {e}")

    async def send_metric_update(self, metric_type: str, data: Dict):
        """Send metric update to subscribed clients"""
        await self.broadcast(metric_type, data)

    async def cleanup(self):
        """Cleanup resources on shutdown"""
        # Cancel background task
        if self.background_task:
            self.background_task.cancel()
            try:
                await self.background_task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        for websocket in self.active_connections[:]:
            await websocket.close()
            self.disconnect(websocket)

        # Close Redis connections
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()

        logger.info("WebSocket manager cleaned up")
