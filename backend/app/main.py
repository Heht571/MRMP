from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1 import api_router
from app.api.v2 import api_router as api_router_v2
from app.db.database import async_engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


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
