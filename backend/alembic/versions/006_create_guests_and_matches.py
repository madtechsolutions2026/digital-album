"""Create guests and guest_matches tables for QR registration and match review

Revision ID: 006
Revises: 005
Create Date: 2026-11-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create guests table
    op.create_table(
        "guests",
        sa.Column("guest_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("selfie_path", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="registered", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("guest_id")
    )
    op.create_index(op.f("ix_guests_event_id"), "guests", ["event_id"], unique=False)
    op.create_index(op.f("ix_guests_guest_id"), "guests", ["guest_id"], unique=False)
    op.create_index(op.f("ix_guests_status"), "guests", ["status"], unique=False)

    # Create guest_matches table
    op.create_table(
        "guest_matches",
        sa.Column("match_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("photo_id", sa.Integer(), nullable=False),
        sa.Column("similarity", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), server_default="pending_review", nullable=False),
        sa.Column("bounding_box", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.event_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.guest_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["photo_id"], ["photos.photo_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("match_id")
    )
    op.create_index(op.f("ix_guest_matches_event_id"), "guest_matches", ["event_id"], unique=False)
    op.create_index(op.f("ix_guest_matches_guest_id"), "guest_matches", ["guest_id"], unique=False)
    op.create_index(op.f("ix_guest_matches_match_id"), "guest_matches", ["match_id"], unique=False)
    op.create_index(op.f("ix_guest_matches_photo_id"), "guest_matches", ["photo_id"], unique=False)
    op.create_index(op.f("ix_guest_matches_status"), "guest_matches", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("guest_matches")
    op.drop_table("guests")
