import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

# Prometheus metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "HTTP requests in progress",
)

health_score_gauge = Gauge(
    "network_health_score",
    "Current network health score (0-100)",
)

active_websocket_connections = Gauge(
    "active_websocket_connections",
    "Number of active WebSocket connections",
)

mev_revenue_total = Counter(
    "mev_revenue_total_eth",
    "Total MEV revenue extracted in ETH",
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track in-progress requests
        http_requests_in_progress.inc()

        # Track request duration
        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Record metrics
            endpoint = request.url.path
            method = request.method
            status = response.status_code

            http_requests_total.labels(
                method=method, endpoint=endpoint, status_code=status
            ).inc()
            http_request_duration_seconds.labels(
                method=method, endpoint=endpoint
            ).observe(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time

            # Record error metrics
            http_requests_total.labels(
                method=request.method, endpoint=request.url.path, status_code=500
            ).inc()
            http_request_duration_seconds.labels(
                method=request.method, endpoint=request.url.path
            ).observe(duration)

            raise e

        finally:
            http_requests_in_progress.dec()


async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")
