-- TimescaleDB 初始化脚本
-- 此脚本需要在应用启动时或手动执行一次

-- 1. 启用 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 2. 检查 timeseries_data 表是否存在并转换为超表
-- 注意: 只有在表创建完成后才能转换为超表

DO $$
BEGIN
    -- 检查是否是普通表
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'timeseries_data'
    ) AND NOT EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'timeseries_data'
    ) THEN
        -- 转换为超表
        SELECT create_hypertable('timeseries_data', 'timestamp',
            if_not_exists => TRUE,
            migrate_data => FALSE
        );

        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_timeseries_instance_attr
        ON timeseries_data (instance_id, attribute_name, timestamp DESC);

        RAISE NOTICE 'TimeseriesData table converted to hypertable successfully';
    END IF;
EXCEPTION
    WHEN undefined_table THEN
        RAISE NOTICE 'timeseries_data table does not exist yet, will be created on app startup';
    WHEN others THEN
        RAISE WARNING 'TimescaleDB conversion failed: %', SQLERRM;
END
$$;

-- 3. 可选: 创建连续聚合视图 (用于高性能查询)
-- 示例: 按小时聚合的 CPU 使用率视图
/*
CREATE MATERIALIZED VIEW IF NOT EXISTS timeseries_hourly_cpu
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    instance_id,
    attribute_name,
    avg((value->>'cpu')::float) AS cpu_avg,
    max((value->>'cpu')::float) AS cpu_max,
    min((value->>'cpu')::float) AS cpu_min,
    count(*) AS sample_count
FROM timeseries_data
WHERE value ? 'cpu'
GROUP BY bucket, instance_id, attribute_name;

-- 创建压缩策略 (可选，提升存储效率)
ALTER MATERIALIZED VIEW timeseries_hourly_cpu SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'instance_id, attribute_name'
);

-- 添加压缩策略: 30天后压缩
SELECT add_compression_policy('timeseries_hourly_cpu', INTERVAL '30 days');
*/