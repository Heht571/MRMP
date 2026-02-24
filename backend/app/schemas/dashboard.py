from typing import Optional, Dict, Any, List
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from app.models.dashboard import WidgetType

class WidgetBase(BaseModel):
    name: str = Field(..., description="组件名称")
    type: WidgetType = Field(..., description="组件类型")
    config: Dict[str, Any] = Field(default={}, description="组件配置")
    layout: Dict[str, Any] = Field(default={}, description="布局配置")
    is_active: bool = True

class WidgetCreate(WidgetBase):
    pass

class WidgetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[WidgetType] = None
    config: Optional[Dict[str, Any]] = None
    layout: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class WidgetResponse(WidgetBase):
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        from_attributes = True

class DashboardLayoutUpdate(BaseModel):
    """批量更新布局"""
    widgets: List[Dict[str, Any]]  # List of {id: uuid, layout: {...}}
