"""Add composite indexes for performance optimization

Revision ID: perf_optimization_001
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'perf_optimization_001'
down_revision = None  # Set to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Relation Definition 复合索引
    op.create_index(
        'ix_relation_definitions_source_target',
        'relation_definitions',
        ['source_model_id', 'target_model_id'],
        if_not_exists=True
    )

    # Instance Relation 复合索引
    op.create_index(
        'ix_instance_relations_source_target',
        'instance_relations',
        ['source_instance_id', 'target_instance_id'],
        if_not_exists=True
    )

    op.create_index(
        'ix_instance_relations_def_source',
        'instance_relations',
        ['relation_definition_id', 'source_instance_id'],
        if_not_exists=True
    )


def downgrade() -> None:
    op.drop_index('ix_instance_relations_def_source', table_name='instance_relations')
    op.drop_index('ix_instance_relations_source_target', table_name='instance_relations')
    op.drop_index('ix_relation_definitions_source_target', table_name='relation_definitions')