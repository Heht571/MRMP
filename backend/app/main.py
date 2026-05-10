from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.config import settings
from app.api.v1 import api_router
from app.api.v2 import api_router as api_router_v2
from app.db.database import async_engine, Base
from app.models.timeseries import TimeseriesData


async def init_timeseries(db):
    """初始化 TimescaleDB (如果可用)"""
    try:
        # 尝试创建扩展 (可能已经存在)
        await db.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))

        # 检查表是否存在
        result = await db.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_name = 'timeseries_data'
            ) as table_exists
        """))
        table_exists = result.scalar()

        if table_exists:
            # 尝试转换为超表 (如果已经是超表会报错但不影响)
            try:
                await db.execute(text("""
                    SELECT create_hypertable('timeseries_data', 'timestamp',
                        if_not_exists => TRUE,
                        migrate_data => FALSE
                    )
                """))
                print("TimescaleDB hypertable created successfully")
            except Exception as e:
                # 超表已存在或环境不支持 TimescaleDB，使用普通表
                print(f"Note: Using regular PostgreSQL table (TimescaleDB not available): {e}")

            # 创建索引 (如果不存在)
            try:
                await db.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_ts_instance_attr_time
                    ON timeseries_data (instance_id, attribute_name, timestamp DESC)
                """))
            except Exception:
                pass

            print("Timeseries data table initialized")

    except Exception as e:
        # 不影响主流程，降级为普通 PostgreSQL 表
        print(f"Warning: TimescaleDB initialization skipped (using regular table): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时: 创建所有表并初始化 TimescaleDB
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

        # 尝试初始化 TimescaleDB (不影响主流程)
        from app.db.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await init_timeseries(session)
            await session.commit()

    yield

    # 关闭时: 清理资源
    await async_engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(api_router_v2, prefix="/api/v2")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}


@app.get("/")
async def root():
    return {
        "message": "MRMP - 元资源管理平台 API",
        "docs": "/api/docs",
        "version": settings.VERSION
    }