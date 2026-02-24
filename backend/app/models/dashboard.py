import uuid
import enum
from sqlalchemy import Column, String, Integer, JSON, Boolean, DateTime, func, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base

class WidgetType(str, enum.Enum):
    CHART = "chart"
    STAT = "stat"
    LIST = "list"
    CUSTOM = "custom"

class DashboardWidget(Base):
    """仪表盘组件配置表"""
    __tablename__ = "dashboard_widgets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="组件名称")
    type = Column(String(50), nullable=False, comment="组件类型: chart, stat, list, custom")
    
    # 组件配置 (JSONB)
    # {
    #   "chart_type": "bar", // for chart
    #   "model_id": "...", 
    #   "aggregation": "count",
    #   "dimension": "status",
    #   "refresh_interval": 60
    # }
    config = Column(JSONB, nullable=False, default={}, comment="组件详细配置")
    
    # 布局配置 (JSONB)
    # {
    #   "x": 0, "y": 0, "w": 4, "h": 2
    # }
    layout = Column(JSONB, nullable=False, default={}, comment="布局位置配置")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
