from fastapi import APIRouter
from app.api.v1.endpoints import instances, login

api_router = APIRouter()
api_router.include_router(login.router, tags=["认证"])
api_router.include_router(instances.router, prefix="/instances", tags=["资源实例"])
