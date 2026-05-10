"""Add is_root_model to models table

Revision ID: add_root_model_flag
Revises: add_model_relations
Create Date: 2026-05-06
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_root_model_flag'
down_revision = None  # Adjust this to the latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('models', sa.Column('is_root_model', sa.Boolean(), server_default='false', nullable=False))


def downgrade() -> None:
    op.drop_column('models', 'is_root_model')