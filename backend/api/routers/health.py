from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.etl.processors.health_score_calculator import NetworkHealthCalculator
from backend.models.database import get_db
from backend.models.metrics import NetworkHealthScore

router = APIRouter()


@router.get("/score")
async def get_network_health_score(db: Session = Depends(get_db)):
    """Get current network health score"""
    # Try to get recent calculated score
    recent_score = (
        db.query(NetworkHealthScore)
        .order_by(NetworkHealthScore.timestamp.desc())
        .first()
    )

    # If no recent score or it's older than 5 minutes, calculate new one
    if not recent_score or recent_score.timestamp < datetime.utcnow() - timedelta(
        minutes=5
    ):
        calculator = NetworkHealthCalculator()
        health_data = await calculator.calculate_health_score(db)

        # Save to database
        new_score = NetworkHealthScore(
            overall_score=health_data["overall_score"],
            gas_score=health_data["gas_score"],
            congestion_score=health_data["congestion_score"],
            block_time_score=health_data["block_time_score"],
        )
        db.add(new_score)
        db.commit()

        return health_data

    return {
        "timestamp": recent_score.timestamp,
        "overall_score": recent_score.overall_score,
        "gas_score": recent_score.gas_score,
        "congestion_score": recent_score.congestion_score,
        "block_time_score": recent_score.block_time_score,
        "health_status": _get_health_status(recent_score.overall_score),
    }


@router.get("/history")
async def get_health_score_history(db: Session = Depends(get_db), hours: int = 24):
    """Get health score history"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    scores = (
        db.query(NetworkHealthScore)
        .filter(NetworkHealthScore.timestamp >= start_time)
        .order_by(NetworkHealthScore.timestamp)
        .all()
    )

    return {
        "period_hours": hours,
        "scores": [
            {
                "timestamp": score.timestamp,
                "overall_score": score.overall_score,
                "health_status": _get_health_status(score.overall_score),
            }
            for score in scores
        ],
    }


def _get_health_status(score: float) -> str:
    """Get health status label"""
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Poor"
    else:
        return "Critical"
