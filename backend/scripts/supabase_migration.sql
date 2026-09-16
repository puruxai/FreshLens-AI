-- ==============================================================================
-- FreshLens AI Food Freshness Monitoring Platform - Supabase PostgreSQL Migration
-- Migration Target: Supabase PostgreSQL (Transaction Pooler / Direct Connection)
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. ENUM TYPES
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
        CREATE TYPE userrole AS ENUM (
            'ADMIN',
            'CONSUMER',
            'RETAIL_MANAGER',
            'WAREHOUSE_OPERATOR',
            'QUALITY_INSPECTOR'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'batchstatus') THEN
        CREATE TYPE batchstatus AS ENUM (
            'FRESH',
            'WARNING',
            'SPOILED'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'inspectionstatus') THEN
        CREATE TYPE inspectionstatus AS ENUM (
            'PENDING',
            'PASSED',
            'WARNING',
            'REJECTED',
            'QUARANTINED'
        );
    END IF;
END $$;

-- 3. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    full_name VARCHAR,
    role userrole NOT NULL DEFAULT 'CONSUMER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- 4. BATCHES TABLE
CREATE TABLE IF NOT EXISTS batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_number VARCHAR NOT NULL,
    supplier_name VARCHAR,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_batches_batch_number ON batches(batch_number);

-- 5. INVENTORY ITEMS TABLE
CREATE TABLE IF NOT EXISTS inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    batch_id UUID REFERENCES batches(id) ON DELETE SET NULL,
    quantity DOUBLE PRECISION NOT NULL,
    unit VARCHAR NOT NULL,
    packaging_type VARCHAR,
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expiry_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status batchstatus NOT NULL DEFAULT 'FRESH',
    storage_location VARCHAR,
    created_by_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_inventory_items_name ON inventory_items(name);
CREATE INDEX IF NOT EXISTS ix_inventory_items_category ON inventory_items(category);

-- 6. QUALITY INSPECTIONS TABLE
CREATE TABLE IF NOT EXISTS quality_inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES inventory_items(id) ON DELETE SET NULL,
    batch_id UUID REFERENCES batches(id) ON DELETE SET NULL,
    inspector_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_name VARCHAR NOT NULL,
    category VARCHAR NOT NULL,
    packaging_type VARCHAR NOT NULL DEFAULT 'None',
    storage_location VARCHAR NOT NULL DEFAULT 'Ambient Room',
    storage_temperature DOUBLE PRECISION NOT NULL DEFAULT 20.0,
    humidity DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    air_circulation VARCHAR NOT NULL DEFAULT 'Medium',
    light_exposure VARCHAR NOT NULL DEFAULT 'Low',
    storage_duration_days DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    image_url VARCHAR,
    ai_predicted_class VARCHAR NOT NULL DEFAULT 'FRESH',
    ai_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    freshness_score DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    predicted_shelf_life_days DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    quality_classification VARCHAR NOT NULL DEFAULT 'Fresh',
    mold_detected BOOLEAN NOT NULL DEFAULT FALSE,
    bruising_detected BOOLEAN NOT NULL DEFAULT FALSE,
    damage_detected BOOLEAN NOT NULL DEFAULT FALSE,
    color_degradation DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    texture_roughness DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    status inspectionstatus NOT NULL DEFAULT 'PASSED',
    remarks TEXT,
    action_taken VARCHAR,
    inspected_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_quality_inspections_inspected_at ON quality_inspections(inspected_at);
CREATE INDEX IF NOT EXISTS ix_quality_inspections_status ON quality_inspections(status);

-- 7. SUPABASE ROW LEVEL SECURITY (RLS) POLICIES
-- Architecture Security Enforcement:
-- 1. The Next.js frontend routes ALL data operations exclusively through the FastAPI backend (/api/v1/*).
-- 2. The FastAPI backend connects via DATABASE_URL as the PostgreSQL owner (postgres/service_role) and BYPASSES RLS.
-- 3. Row Level Security below explicitly DENIES all direct external/anonymous queries via Supabase PostgREST.

ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_inspections ENABLE ROW LEVEL SECURITY;

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
END $$;

-- 7.1 USERS TABLE: Lock down direct PostgREST access (prevents leaking hashed_password)
CREATE POLICY users_postgrest_block ON users 
    FOR ALL 
    USING (auth.role() = 'service_role') 
    WITH CHECK (auth.role() = 'service_role');

-- 7.2 BATCHES TABLE: Lock down direct PostgREST access
CREATE POLICY batches_postgrest_block ON batches 
    FOR ALL 
    USING (auth.role() = 'service_role') 
    WITH CHECK (auth.role() = 'service_role');

-- 7.3 INVENTORY ITEMS TABLE: Lock down direct PostgREST access
CREATE POLICY inventory_postgrest_block ON inventory_items 
    FOR ALL 
    USING (auth.role() = 'service_role') 
    WITH CHECK (auth.role() = 'service_role');

-- 7.4 QUALITY INSPECTIONS TABLE: Lock down direct PostgREST access
-- 8. IMAGE ANALYSES TABLE
CREATE TABLE IF NOT EXISTS image_analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id VARCHAR NOT NULL,
    filename VARCHAR NOT NULL,
    file_url VARCHAR NOT NULL,
    freshness_score DOUBLE PRECISION NOT NULL,
    color_degradation DOUBLE PRECISION NOT NULL,
    texture_roughness DOUBLE PRECISION NOT NULL,
    mold_detected BOOLEAN NOT NULL DEFAULT FALSE,
    mold_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    bruising_detected BOOLEAN NOT NULL DEFAULT FALSE,
    bruising_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    damage_detected BOOLEAN NOT NULL DEFAULT FALSE,
    damage_confidence DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    classification_label VARCHAR NOT NULL DEFAULT 'FRESH',
    status_message VARCHAR NOT NULL DEFAULT 'Normal classification',
    analyzed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_image_analyses_item_id ON image_analyses(item_id);

-- 9. STORAGE READINGS TABLE
CREATE TABLE IF NOT EXISTS storage_readings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id VARCHAR NOT NULL,
    warehouse_zone VARCHAR NOT NULL,
    temperature DOUBLE PRECISION NOT NULL,
    humidity DOUBLE PRECISION NOT NULL,
    air_circulation VARCHAR NOT NULL DEFAULT 'Medium',
    light_exposure VARCHAR NOT NULL DEFAULT 'Low',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_storage_readings_item_id ON storage_readings(item_id);

-- 10. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR,
    role VARCHAR,
    title VARCHAR NOT NULL,
    message VARCHAR NOT NULL,
    type VARCHAR NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS ix_notifications_role ON notifications(role);

-- 11. NOTIFICATION PREFERENCES TABLE
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR NOT NULL UNIQUE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    min_freshness_threshold DOUBLE PRECISION NOT NULL DEFAULT 50.0,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_notification_preferences_user_id ON notification_preferences(user_id);

-- 12. SYSTEM LOGS TABLE
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR,
    role VARCHAR,
    event_type VARCHAR NOT NULL,
    details VARCHAR NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_system_logs_event_type ON system_logs(event_type);

-- 13. ADDITIONAL RLS POLICIES FOR NEW TABLES
ALTER TABLE image_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE system_logs ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    DROP POLICY IF EXISTS image_analyses_postgrest_block ON image_analyses;
    DROP POLICY IF EXISTS storage_readings_postgrest_block ON storage_readings;
    DROP POLICY IF EXISTS notifications_postgrest_block ON notifications;
    DROP POLICY IF EXISTS notification_preferences_postgrest_block ON notification_preferences;
    DROP POLICY IF EXISTS system_logs_postgrest_block ON system_logs;
END $$;

CREATE POLICY image_analyses_postgrest_block ON image_analyses FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY storage_readings_postgrest_block ON storage_readings FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY notifications_postgrest_block ON notifications FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY notification_preferences_postgrest_block ON notification_preferences FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');
CREATE POLICY system_logs_postgrest_block ON system_logs FOR ALL USING (auth.role() = 'service_role') WITH CHECK (auth.role() = 'service_role');




