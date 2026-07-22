"""create photos table

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create photos table."""
    op.create_table(
        'photos',
        sa.Column('photo_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False, comment='Foreign key to the event this photo belongs to'),
        sa.Column('file_path', sa.String(length=512), nullable=False, comment='Relative path to the stored image file'),
        sa.Column('photo_metadata', sa.JSON(), nullable=True, comment='Additional metadata about the photo (dimensions, format, etc.)'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when the photo was uploaded'),
        sa.ForeignKeyConstraint(['event_id'], ['events.event_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('photo_id'),
        sa.UniqueConstraint('file_path', name='uq_photos_file_path')
    )
    op.create_index(op.f('ix_photos_photo_id'), 'photos', ['photo_id'], unique=False)
    op.create_index(op.f('ix_photos_event_id'), 'photos', ['event_id'], unique=False)
    op.create_index(op.f('ix_photos_uploaded_at'), 'photos', ['uploaded_at'], unique=False)


def downgrade() -> None:
    """Drop photos table."""
    op.drop_index(op.f('ix_photos_uploaded_at'), table_name='photos')
    op.drop_index(op.f('ix_photos_event_id'), table_name='photos')
    op.drop_index(op.f('ix_photos_photo_id'), table_name='photos')
    op.drop_table('photos')
