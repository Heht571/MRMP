from typing import List, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_async_db
from app.schemas.dashboard import WidgetCreate, WidgetUpdate, WidgetResponse, DashboardLayoutUpdate
from app.services.dashboard_service import DashboardService

router = APIRouter()

@router.get("/widgets", response_model=List[WidgetResponse])
async def get_widgets(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_async_db)
):
    """获取仪表盘组件列表"""
    widgets = await DashboardService.get_widgets(db, skip=skip, limit=limit)
    return widgets

@router.post("/widgets", response_model=WidgetResponse)
async def create_widget(
    widget_in: WidgetCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建仪表盘组件"""
    return await DashboardService.create_widget(db, widget_in)

@router.put("/widgets/layout", response_model=bool)
async def update_layout(
    layout_update: DashboardLayoutUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """批量更新组件布局"""
    return await DashboardService.update_layout(db, layout_update.widgets)

@router.put("/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    widget_id: UUID,
    widget_in: WidgetUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新组件配置"""
    widget = await DashboardService.update_widget(db, widget_id, widget_in)
    if not widget:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget

@router.delete("/widgets/{widget_id}", response_model=bool)
async def delete_widget(
    widget_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """删除组件"""
    success = await DashboardService.delete_widget(db, widget_id)
    if not success:
        raise HTTPException(status_code=404, detail="Widget not found")
    return True

@router.get("/widgets/{widget_id}/data")
async def get_widget_data(
    widget_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """获取组件数据"""
    data = await DashboardService.get_widget_data(db, widget_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return data
