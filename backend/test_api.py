import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.models.database import Base, engine

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_get_gas_metrics():
    """Test gas metrics endpoint"""
    response = client.get("/api/v1/metrics/gas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_network_health():
    """Test network health endpoint"""
    response = client.get("/api/v1/health/score")
    assert response.status_code == 200
    data = response.json()
    assert "overall_score" in data
    assert 0 <= data["overall_score"] <= 100


def test_get_l2_comparison():
    """Test L2 comparison endpoint"""
    response = client.get("/api/v1/l2/comparison")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)


def test_get_mev_impact():
    """Test MEV impact endpoint"""
    response = client.get("/api/v1/mev/impact?hours=24")
    assert response.status_code == 200
    data = response.json()
    assert "total_mev_revenue_eth" in data


@pytest.mark.asyncio
async def test_websocket_connection():
    """Test WebSocket connection"""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection"
        assert data["status"] == "connected"

        # Test subscription
        websocket.send_json(
            {"action": "subscribe", "channels": ["gas_prices", "network_health"]}
        )

        response = websocket.receive_json()
        assert response["type"] == "subscribed"
        assert len(response["channels"]) == 2
