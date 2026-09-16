"""Add batches, inventory_items, and quality_inspections with Supabase RLS

Revision ID: c9f623910ab1
Revises: b7f5218dceb0
Create Date: 2026-09-16 08:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c9f623910ab1'
down_revision: Union[str, None] = 'b7f5218dceb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Clean up legacy inventory_batches if present
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'inventory_batches' in tables:
        op.execute('DROP TABLE IF EXISTS inventory_batches CASCADE')

    # 2. Create batches table
    if 'batches' not in tables:
        op.create_table(
            'batches',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('batch_number', sa.String(), nullable=False),
            sa.Column('supplier_name', sa.String(), nullable=True),
            sa.Column('received_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_batches_batch_number'), 'batches', ['batch_number'], unique=True)

    # 3. Create Enum types if Postgres dialect
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        batch_status_enum = postgresql.ENUM('FRESH', 'WARNING', 'SPOILED', name='batchstatus')
        batch_status_enum.create(bind, checkfirst=True)

        inspection_status_enum = postgresql.ENUM('PENDING', 'PASSED', 'WARNING', 'REJECTED', 'QUARANTINED', name='inspectionstatus')
        inspection_status_enum.create(bind, checkfirst=True)

    # 4. Create inventory_items table
    if 'inventory_items' not in tables:
        op.create_table(
            'inventory_items',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('batch_id', sa.UUID(), nullable=True),
            sa.Column('quantity', sa.Float(), nullable=False),
            sa.Column('unit', sa.String(), nullable=False),
            sa.Column('packaging_type', sa.String(), nullable=True),
            sa.Column('entry_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('expiry_date', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.Enum('FRESH', 'WARNING', 'SPOILED', name='batchstatus'), nullable=False),
            sa.Column('storage_location', sa.String(), nullable=True),
            sa.Column('created_by_id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_inventory_items_category'), 'inventory_items', ['category'], unique=False)
        op.create_index(op.f('ix_inventory_items_name'), 'inventory_items', ['name'], unique=False)

    # 5. Create quality_inspections table
    if 'quality_inspections' not in tables:
        op.create_table(
            'quality_inspections',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('item_id', sa.UUID(), nullable=True),
            sa.Column('batch_id', sa.UUID(), nullable=True),
            sa.Column('inspector_id', sa.UUID(), nullable=False),
            sa.Column('product_name', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('packaging_type', sa.String(), nullable=False, server_default='None'),
            sa.Column('storage_location', sa.String(), nullable=False, server_default='Ambient Room'),
            sa.Column('storage_temperature', sa.Float(), nullable=False, server_default='20.0'),
            sa.Column('humidity', sa.Float(), nullable=False, server_default='50.0'),
            sa.Column('air_circulation', sa.String(), nullable=False, server_default='Medium'),
            sa.Column('light_exposure', sa.String(), nullable=False, server_default='Low'),
            sa.Column('storage_duration_days', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('image_url', sa.String(), nullable=True),
            sa.Column('ai_predicted_class', sa.String(), nullable=False, server_default='FRESH'),
            sa.Column('ai_confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('freshness_score', sa.Float(), nullable=False, server_default='100.0'),
            sa.Column('predicted_shelf_life_days', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('quality_classification', sa.String(), nullable=False, server_default='Fresh'),
            sa.Column('mold_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('bruising_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('damage_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('color_degradation', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('texture_roughness', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('status', sa.Enum('PENDING', 'PASSED', 'WARNING', 'REJECTED', 'QUARANTINED', name='inspectionstatus'), nullable=False),
            sa.Column('remarks', sa.Text(), nullable=True),
            sa.Column('action_taken', sa.String(), nullable=True),
            sa.Column('inspected_at', sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(['batch_id'], ['batches.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_quality_inspections_inspected_at'), 'quality_inspections', ['inspected_at'], unique=False)
        op.create_index(op.f('ix_quality_inspections_status'), 'quality_inspections', ['status'], unique=False)

    # 6. Apply Row Level Security (RLS) when running on PostgreSQL / Supabase
    if bind.dialect.name == 'postgresql':
        # Enable RLS
        op.execute('ALTER TABLE users ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE batches ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE quality_inspections ENABLE ROW LEVEL SECURITY;')

        # Create production RLS policies safely
        op.execute("""
        DO $$
        BEGIN
            DROP POLICY IF EXISTS users_read_policy ON users;
            DROP POLICY IF EXISTS users_select_policy ON users;
            DROP POLICY IF EXISTS users_write_policy ON users;
            DROP POLICY IF EXISTS users_postgrest_block ON users;

            DROP POLICY IF EXISTS batches_authenticated_policy ON batches;
            DROP POLICY IF EXISTS batches_select_policy ON batches;
            DROP POLICY IF EXISTS batches_write_policy ON batches;
            DROP POLICY IF EXISTS batches_postgrest_block ON batches;

            DROP POLICY IF EXISTS inventory_authenticated_policy ON inventory_items;
            DROP POLICY IF EXISTS inventory_select_policy ON inventory_items;
            DROP POLICY IF EXISTS inventory_write_policy ON inventory_items;
            DROP POLICY IF EXISTS inventory_postgrest_block ON inventory_items;

            DROP POLICY IF EXISTS quality_inspections_policy ON quality_inspections;
            DROP POLICY IF EXISTS quality_inspections_select_policy ON quality_inspections;
            DROP POLICY IF EXISTS quality_inspections_write_policy ON quality_inspections;
            DROP POLICY IF EXISTS quality_inspections_postgrest_block ON quality_inspections;

            -- Explicitly block all external/anonymous PostgREST access while backend connects as DB owner (bypassing RLS)
            CREATE POLICY users_postgrest_block ON users FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY batches_postgrest_block ON batches FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY inventory_postgrest_block ON inventory_items FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY quality_inspections_postgrest_block ON quality_inspections FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
        END $$;
        """)

    # 7. Create migrated tables (image_analyses, storage_readings, notifications, notification_preferences, system_logs)
    if 'image_analyses' not in tables:
        op.create_table(
            'image_analyses',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('item_id', sa.String(), nullable=False),
            sa.Column('filename', sa.String(), nullable=False),
            sa.Column('file_url', sa.String(), nullable=False),
            sa.Column('freshness_score', sa.Float(), nullable=False),
            sa.Column('color_degradation', sa.Float(), nullable=False),
            sa.Column('texture_roughness', sa.Float(), nullable=False),
            sa.Column('mold_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('mold_confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('bruising_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('bruising_confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('damage_detected', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('damage_confidence', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('classification_label', sa.String(), nullable=False, server_default='FRESH'),
            sa.Column('status_message', sa.String(), nullable=False, server_default='Normal classification'),
            sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_image_analyses_item_id'), 'image_analyses', ['item_id'], unique=False)

    if 'storage_readings' not in tables:
        op.create_table(
            'storage_readings',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('item_id', sa.String(), nullable=False),
            sa.Column('warehouse_zone', sa.String(), nullable=False),
            sa.Column('temperature', sa.Float(), nullable=False),
            sa.Column('humidity', sa.Float(), nullable=False),
            sa.Column('air_circulation', sa.String(), nullable=False, server_default='Medium'),
            sa.Column('light_exposure', sa.String(), nullable=False, server_default='Low'),
            sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_storage_readings_item_id'), 'storage_readings', ['item_id'], unique=False)

    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=True),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('message', sa.String(), nullable=False),
            sa.Column('type', sa.String(), nullable=False),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
        op.create_index(op.f('ix_notifications_role'), 'notifications', ['role'], unique=False)

    if 'notification_preferences' not in tables:
        op.create_table(
            'notification_preferences',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=False),
            sa.Column('email_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('in_app_enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('min_freshness_threshold', sa.Float(), nullable=False, server_default='50.0'),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_notification_preferences_user_id'), 'notification_preferences', ['user_id'], unique=True)

    if 'system_logs' not in tables:
        op.create_table(
            'system_logs',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('user_id', sa.String(), nullable=True),
            sa.Column('role', sa.String(), nullable=True),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('details', sa.String(), nullable=False),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_system_logs_event_type'), 'system_logs', ['event_type'], unique=False)

    if bind.dialect.name == 'postgresql':
        op.execute('ALTER TABLE image_analyses ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE storage_readings ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;')
        op.execute('ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;')
        op.execute("""
        DO $$
        BEGIN
            CREATE POLICY image_analyses_postgrest_block ON image_analyses FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY storage_readings_postgrest_block ON storage_readings FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY notifications_postgrest_block ON notifications FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY notification_preferences_postgrest_block ON notification_preferences FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
            CREATE POLICY system_logs_postgrest_block ON system_logs FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
        EXCEPTION WHEN OTHERS THEN NULL;
        END $$;
        """)




def downgrade() -> None:
    op.drop_index(op.f('ix_quality_inspections_status'), table_name='quality_inspections')
    op.drop_index(op.f('ix_quality_inspections_inspected_at'), table_name='quality_inspections')
    op.drop_table('quality_inspections')
    op.drop_index(op.f('ix_inventory_items_name'), table_name='inventory_items')
    op.drop_index(op.f('ix_inventory_items_category'), table_name='inventory_items')
    op.drop_table('inventory_items')
    op.drop_index(op.f('ix_batches_batch_number'), table_name='batches')
    op.drop_table('batches')
