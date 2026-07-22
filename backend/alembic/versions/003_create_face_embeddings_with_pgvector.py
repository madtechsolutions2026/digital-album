"""create face_embeddings table with pgvector

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pgvector extension and face_embeddings table."""
    
    # Create pgvector extension if it doesn't exist
    # This requires superuser privileges in PostgreSQL
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create face_embeddings table
    op.create_table(
        'face_embeddings',
        sa.Column('embedding_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('photo_id', sa.Integer(), nullable=False, comment='Foreign key to the photo this face belongs to'),
        sa.Column('embedding_vector', Vector(512), nullable=False, comment='512-dimensional face embedding vector from InsightFace'),
        sa.Column('bounding_box', sa.JSON(), nullable=False, comment='Face bounding box coordinates {x1, y1, x2, y2}'),
        sa.Column('confidence_score', sa.Float(), nullable=False, comment='Face detection confidence score (0.0 to 1.0)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when the embedding was created'),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.photo_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('embedding_id'),
        sa.CheckConstraint('confidence_score >= 0.0 AND confidence_score <= 1.0', name='face_embeddings_confidence_range')
    )
    
    # Create indexes
    op.create_index(op.f('ix_face_embeddings_embedding_id'), 'face_embeddings', ['embedding_id'], unique=False)
    op.create_index(op.f('ix_face_embeddings_photo_id'), 'face_embeddings', ['photo_id'], unique=False)
    
    # Create HNSW index on embedding_vector for fast similarity search
    # HNSW (Hierarchical Navigable Small World) is optimal for high-dimensional vector search
    # m=16: number of connections per layer (higher = better recall, more memory)
    # ef_construction=200: size of dynamic candidate list (higher = better index quality, slower build)
    op.execute("""
        CREATE INDEX ix_face_embeddings_vector_hnsw 
        ON face_embeddings 
        USING hnsw (embedding_vector vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)


def downgrade() -> None:
    """Drop face_embeddings table and pgvector extension."""
    
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS ix_face_embeddings_vector_hnsw")
    op.drop_index(op.f('ix_face_embeddings_photo_id'), table_name='face_embeddings')
    op.drop_index(op.f('ix_face_embeddings_embedding_id'), table_name='face_embeddings')
    
    # Drop table
    op.drop_table('face_embeddings')
    
    # Note: We don't drop the vector extension in downgrade as other migrations might use it
    # and it's safe to leave extensions installed
    # If you really need to drop it: op.execute("DROP EXTENSION IF EXISTS vector")
