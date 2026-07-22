"""create events table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create events table."""
    op.create_table(
        'events',
        sa.Column('event_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment="Name of the event (e.g., 'Smith Wedding 2024')"),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False, comment='Date and time of the event'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when the record was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when the record was last updated'),
        sa.PrimaryKeyConstraint('event_id'),
        sa.CheckConstraint('length(name) > 0', name='events_name_not_empty')
    )
    op.create_index(op.f('ix_events_event_id'), 'events', ['event_id'], unique=False)


def downgrade() -> None:
    """Drop events table."""
    op.drop_index(op.f('ix_events_event_id'), table_name='events')
    op.drop_table('events')
