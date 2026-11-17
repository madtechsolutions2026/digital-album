"""record the InsightFace model pack used for each embedding

Revision ID: 005
Revises: 004
Create Date: 2026-09-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add model provenance and mark existing rows as the legacy default."""
    op.add_column(
        "face_embeddings",
        sa.Column(
            "model_name",
            sa.String(length=64),
            nullable=False,
            server_default="buffalo_s",
            comment="InsightFace model pack used to create this embedding",
        ),
    )
    op.create_index(
        op.f("ix_face_embeddings_model_name"),
        "face_embeddings",
        ["model_name"],
        unique=False,
    )


def downgrade() -> None:
    """Remove model provenance metadata."""
    op.drop_index(op.f("ix_face_embeddings_model_name"), table_name="face_embeddings")
    op.drop_column("face_embeddings", "model_name")
