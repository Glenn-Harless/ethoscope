import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.websockets import WebSocketDisconnect

from backend.api.middleware.auth import APIKeyAuth
from backend.api.middleware.monitoring import MetricsMiddleware
from backend.api.middleware.rate_limit import RateLimiter
from backend.api.routers import admin, health, l2_comparison, metrics, mev
from backend.api.websocket import WebSocketManager
from backend.etl.pipeline import ETLPipeline
from backend.models.database import SessionLocal
from backend.models.metrics import NetworkHealthScore

logger = logging.getLogger(__name__)

# Global instances
etl_pipeline = None
ws_manager = None
rate_limiter = None
auth = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global etl_pipeline, ws_manager, rate_limiter, auth

    # Startup
    logger.info("Starting API server...")

    # Initialize services
    ws_manager = WebSocketManager()
    rate_limiter = RateLimiter(os.getenv("REDIS_URL", "redis://localhost:6379"))
    auth = APIKeyAuth()

    # Start ETL pipeline with WebSocket manager
    etl_pipeline = ETLPipeline(ws_manager=ws_manager)
    asyncio.create_task(etl_pipeline.run())

    # Start background tasks
    asyncio.create_task(update_health_metrics())

    yield

    # Shutdown
    logger.info("Shutting down API server...")
    if etl_pipeline:
        await etl_pipeline.stop()
    if ws_manager:
        await ws_manager.cleanup()


async def update_health_metrics():
    """Update Prometheus health metrics"""
    from backend.api.middleware.monitoring import health_score_gauge

    while True:
        try:
            # Get latest health score
            db = SessionLocal()
            health_score = (
                db.query(NetworkHealthScore)
                .order_by(NetworkHealthScore.timestamp.desc())
                .first()
            )
            if health_score:
                health_score_gauge.set(health_score.overall_score)
            db.close()
        except Exception as e:
            logger.error(f"Error updating health metrics: {e}")

        await asyncio.sleep(60)  # Update every minute


app = FastAPI(
    title="Ethereum Network Health Monitor API",
    description="Real-time Ethereum network health monitoring with ML predictions",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add middleware
app.add_middleware(MetricsMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add rate limit headers to responses
@app.middleware("http")
async def add_rate_limit_headers(request: Request, call_next):
    response = await call_next(request)

    # Add rate limit headers if they exist
    if hasattr(request.state, "rate_limit_headers"):
        for header, value in request.state.rate_limit_headers.items():
            response.headers[header] = value

    return response


# Include routers with auth dependencies
from backend.api.dependencies import verify_request  # noqa: E402

app.include_router(
    metrics.router,
    prefix="/api/v1/metrics",
    tags=["metrics"],
    dependencies=[Depends(verify_request)],
)
app.include_router(
    health.router,
    prefix="/api/v1/health",
    tags=["health"],
    dependencies=[Depends(verify_request)],
)
app.include_router(
    l2_comparison.router,
    prefix="/api/v1/l2",
    tags=["l2"],
    dependencies=[Depends(verify_request)],
)
app.include_router(
    mev.router,
    prefix="/api/v1/mev",
    tags=["mev"],
    dependencies=[Depends(verify_request)],
)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Ethereum Network Health Monitor API",
        "version": "2.0.0",
        "docs": "/api/docs",
        "health": "/api/v1/health/score",
    }


@app.get("/api/v1/status")
async def get_api_status():
    """Get API status (public endpoint)"""
    return {"status": "operational", "timestamp": datetime.utcnow(), "version": "2.0.0"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            # Process subscription requests
            await ws_manager.handle_message(websocket, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
