"""Add model_relations table

Revision ID: add_model_relations
Revises: v2_meta_model
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_model_relations'
down_revision = 'v2_meta_model'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'model_relations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('relation_name', sa.String(100), nullable=False),
        sa.Column('inverse_name', sa.String(100), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('min_cardinality', sa.Integer, default=0),
        sa.Column('max_cardinality', sa.Integer, default=-1),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('sort_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_model_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_model_id'], ['models.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('source_model_id', 'target_model_id', 'relation_type', name='uq_model_relation'),
    )
    op.create_index('ix_model_relations_source_model_id', 'model_relations', ['source_model_id'])
    op.create_index('ix_model_relations_target_model_id', 'model_relations', ['target_model_id'])


def downgrade():
    op.drop_index('ix_model_relations_target_model_id')
    op.drop_index('ix_model_relations_source_model_id')
    op.drop_table('model_relations')
