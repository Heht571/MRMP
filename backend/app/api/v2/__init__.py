from fastapi import APIRouter
from app.api.v2.endpoints import global_attributes, models, relation_definitions, instance_relations, hierarchy, dashboard, topology

api_router = APIRouter()

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["仪表盘管理"]
)

api_router.include_router(
    global_attributes.router, 
    prefix="/global-attributes", 
    tags=["全局属性"]
)
api_router.include_router(
    models.router, 
    prefix="/models", 
    tags=["模型管理V2"]
)
api_router.include_router(
    relation_definitions.router, 
    prefix="/relation-definitions", 
    tags=["关系定义"]
)
api_router.include_router(
    instance_relations.router, 
    prefix="/instance-relations", 
    tags=["实例关系"]
)
api_router.include_router(
    hierarchy.router, 
    prefix="/hierarchy", 
    tags=["资源层级视图"]
)
api_router.include_router(
    topology.router,
    prefix="/topology",
    tags=["拓扑视图"]
)
