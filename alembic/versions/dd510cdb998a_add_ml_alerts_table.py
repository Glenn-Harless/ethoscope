"""add ml alerts table

Revision ID: dd510cdb998a
Revises: de7fdaa0c9aa
Create Date: 2025-07-31 16:15:18.852348

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "dd510cdb998a"
down_revision: Union[str, Sequence[str], None] = "de7fdaa0c9aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "ml_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("alert_type", sa.String(50), nullable=False),  # anomaly, prediction
        sa.Column("severity", sa.String(20), nullable=False),  # low, medium, high, critical
        sa.Column("metric_name", sa.String(50), nullable=True),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("predicted_value", sa.Float(), nullable=True),
        sa.Column("message", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ml_alerts_timestamp", "ml_alerts", ["timestamp"])
    op.create_index("idx_ml_alerts_type_severity", "ml_alerts", ["alert_type", "severity"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_ml_alerts_type_severity", table_name="ml_alerts")
    op.drop_index("idx_ml_alerts_timestamp", table_name="ml_alerts")
    op.drop_table("ml_alerts")
