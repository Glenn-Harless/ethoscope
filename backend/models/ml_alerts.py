import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class MLAlert(Base):
    """Simple ML-based alerts"""

    __tablename__ = "ml_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    alert_type = Column(String(50), nullable=False)  # anomaly, prediction
    severity = Column(String(20), nullable=False)
    metric_name = Column(String(50))
    metric_value = Column(Float)
    predicted_value = Column(Float)
    message = Column(String(500), nullable=False)
    created_at = Column(DateTime, server_default="now()")
