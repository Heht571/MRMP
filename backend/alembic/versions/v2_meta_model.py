"""Add v2 meta model tables

Revision ID: v2_meta_model
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'v2_meta_model'
down_revision = '75668096e911'
branch_labels = None
depends_on = None


def upgrade():
    # Create global_attributes table
    op.create_table(
        'global_attributes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('label', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('type', sa.Enum('STRING', 'NUMBER', 'ENUM', 'BOOLEAN', 'DATE', 'DATETIME', 'JSON', 'UUID', name='attributetype_v2'), nullable=False),
        sa.Column('is_choice', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_list', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_unique', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_indexed', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_sortable', sa.Boolean(), nullable=True, default=False),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('enum_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('validation_regex', sa.String(500), nullable=True),
        sa.Column('min_value', sa.String(50), nullable=True),
        sa.Column('max_value', sa.String(50), nullable=True),
        sa.Column('is_reference', sa.Boolean(), nullable=True, default=False),
        sa.Column('reference_model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_computed', sa.Boolean(), nullable=True, default=False),
        sa.Column('compute_expr', sa.Text(), nullable=True),
        sa.Column('compute_script', sa.Text(), nullable=True),
        sa.Column('choice_webhook', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('choice_script', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_global_attributes_name', 'global_attributes', ['name'])
    op.create_index('ix_global_attributes_type', 'global_attributes', ['type'])
    
    # Add new columns to models table
    op.add_column('models', sa.Column('unique_key_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('models', sa.Column('show_key_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('models', sa.Column('created_by', sa.String(100), nullable=True))
    op.create_foreign_key('fk_models_unique_key', 'models', 'global_attributes', ['unique_key_id'], ['id'])
    op.create_foreign_key('fk_models_show_key', 'models', 'global_attributes', ['show_key_id'], ['id'])
    
    # Create model_attributes table
    op.create_table(
        'model_attributes',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribute_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_readonly', sa.Boolean(), nullable=True, default=False),
        sa.Column('default_show', sa.Boolean(), nullable=True, default=True),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('group_name', sa.String(50), nullable=True),
        sa.Column('override_label', sa.String(100), nullable=True),
        sa.Column('override_default', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id', 'attribute_id', name='uq_model_attribute'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_id'], ['global_attributes.id'], ondelete='CASCADE')
    )
    op.create_index('ix_model_attributes_model_id', 'model_attributes', ['model_id'])
    
    # Create model_inheritance table
    op.create_table(
        'model_inheritance',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_id', 'child_id', name='uq_model_inheritance'),
        sa.ForeignKeyConstraint(['parent_id'], ['models.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['child_id'], ['models.id'], ondelete='CASCADE')
    )
    
    # Create model_unique_constraints table
    op.create_table(
        'model_unique_constraints',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('attribute_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE')
    )
    op.create_index('ix_model_unique_constraints_model_id', 'model_unique_constraints', ['model_id'])
    
    # Create model_triggers table
    op.create_table(
        'model_triggers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('event_type', sa.Enum('BEFORE_CREATE', 'AFTER_CREATE', 'BEFORE_UPDATE', 'AFTER_UPDATE', 'BEFORE_DELETE', 'AFTER_DELETE', name='triggereventtype'), nullable=False),
        sa.Column('action_type', sa.Enum('WEBHOOK', 'EMAIL', 'SCRIPT', name='triggeractiontype'), nullable=False),
        sa.Column('condition', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('action_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['model_id'], ['models.id'], ondelete='CASCADE')
    )
    op.create_index('ix_model_triggers_model_id', 'model_triggers', ['model_id'])
    
    # Create operation_records table
    op.create_table(
        'operation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operate_type', sa.Enum('CREATE', 'UPDATE', 'DELETE', name='operatetype'), nullable=False),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('origin', sa.String(50), nullable=True),
        sa.Column('ticket_id', sa.String(100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_operation_records_model_id', 'operation_records', ['model_id'])
    op.create_index('ix_operation_records_instance_id', 'operation_records', ['instance_id'])
    op.create_index('ix_operation_records_created_at', 'operation_records', ['created_at'])
    op.create_index('ix_operation_records_created_by', 'operation_records', ['created_by'])
    
    # Create attribute_histories table
    op.create_table(
        'attribute_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attribute_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('attribute_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['record_id'], ['operation_records.id'], ondelete='CASCADE')
    )
    op.create_index('ix_attribute_histories_instance_id', 'attribute_histories', ['instance_id'])
    op.create_index('ix_attribute_histories_attribute_id', 'attribute_histories', ['attribute_id'])
    
    # Create relation_histories table
    op.create_table(
        'relation_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relation_type', sa.String(50), nullable=False),
        sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['record_id'], ['operation_records.id'], ondelete='CASCADE')
    )
    op.create_index('ix_relation_histories_source_id', 'relation_histories', ['source_id'])
    op.create_index('ix_relation_histories_target_id', 'relation_histories', ['target_id'])
    
    # Create trigger_histories table
    op.create_table(
        'trigger_histories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trigger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_success', sa.Boolean(), nullable=True, default=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('response_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['trigger_id'], ['model_triggers.id'], ondelete='CASCADE')
    )
    op.create_index('ix_trigger_histories_trigger_id', 'trigger_histories', ['trigger_id'])
    op.create_index('ix_trigger_histories_instance_id', 'trigger_histories', ['instance_id'])
    
    # Add foreign key for global_attributes.reference_model_id
    op.create_foreign_key('fk_global_attributes_reference_model', 'global_attributes', 'models', ['reference_model_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_global_attributes_reference_model', 'global_attributes', type_='foreignkey')
    op.drop_table('trigger_histories')
    op.drop_table('relation_histories')
    op.drop_table('attribute_histories')
    op.drop_table('operation_records')
    op.drop_table('model_triggers')
    op.drop_table('model_unique_constraints')
    op.drop_table('model_inheritance')
    op.drop_table('model_attributes')
    op.drop_constraint('fk_models_show_key', 'models', type_='foreignkey')
    op.drop_constraint('fk_models_unique_key', 'models', type_='foreignkey')
    op.drop_column('models', 'created_by')
    op.drop_column('models', 'show_key_id')
    op.drop_column('models', 'unique_key_id')
    op.drop_table('global_attributes')
    op.execute('DROP TYPE IF EXISTS operatetype')
    op.execute('DROP TYPE IF EXISTS triggeractiontype')
    op.execute('DROP TYPE IF EXISTS triggereventtype')
    op.execute('DROP TYPE IF EXISTS attributetype_v2')
