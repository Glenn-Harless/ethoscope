import time
from collections.abc import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram

# Prometheus metrics
request_count = Counter(
    "ethoscope_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"],
)

request_duration = Histogram(
    "ethoscope_api_request_duration_seconds",
    "API request duration",
    ["method", "endpoint"],
)

active_connections = Gauge("ethoscope_websocket_connections", "Active WebSocket connections")

health_score_gauge = Gauge("ethoscope_network_health_score", "Current network health score")


class MetricsMiddleware:
    """Prometheus metrics middleware"""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time

        request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).inc()

        request_duration.labels(method=request.method, endpoint=request.url.path).observe(duration)

        return response
