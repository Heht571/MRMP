from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.services.topology_service import TopologyService

router = APIRouter()

@router.get("/", response_model=dict)
async def get_topology(
    root_id: UUID,
    depth: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取拓扑图数据
    - root_id: 根节点实例ID
    - depth: 遍历深度 (默认3)
    """
    return await TopologyService.get_topology(db, root_id, depth)
