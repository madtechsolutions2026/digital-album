"""add event access credentials (access_code + password_hash)

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add access_code and password_hash columns, backfilling existing rows."""
    from app.services.auth import generate_access_code, generate_password, hash_password

    # Add as nullable first so existing rows aren't rejected, then backfill
    # and tighten to NOT NULL.
    op.add_column('events', sa.Column(
        'access_code', sa.String(length=12), nullable=True,
        comment="Unique code guests enter to access this event's gallery"
    ))
    op.add_column('events', sa.Column(
        'password_hash', sa.String(length=255), nullable=True,
        comment='Bcrypt hash of the access password (plaintext shown once at creation)'
    ))

    connection = op.get_bind()

    existing_codes = set(
        row[0] for row in connection.execute(
            sa.text("SELECT access_code FROM events WHERE access_code IS NOT NULL")
        )
    )

    event_ids = [row[0] for row in connection.execute(sa.text("SELECT event_id FROM events"))]

    for event_id in event_ids:
        code = generate_access_code()
        while code in existing_codes:
            code = generate_access_code()
        existing_codes.add(code)

        password_hash = hash_password(generate_password())

        connection.execute(
            sa.text(
                "UPDATE events SET access_code = :code, password_hash = :password_hash "
                "WHERE event_id = :event_id"
            ),
            {"code": code, "password_hash": password_hash, "event_id": event_id}
        )

    op.alter_column('events', 'access_code', nullable=False)
    op.alter_column('events', 'password_hash', nullable=False)
    op.create_unique_constraint('uq_events_access_code', 'events', ['access_code'])
    op.create_index(op.f('ix_events_access_code'), 'events', ['access_code'], unique=False)


def downgrade() -> None:
    """Drop access_code and password_hash columns."""
    op.drop_index(op.f('ix_events_access_code'), table_name='events')
    op.drop_constraint('uq_events_access_code', 'events', type_='unique')
    op.drop_column('events', 'password_hash')
    op.drop_column('events', 'access_code')
