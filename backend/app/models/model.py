from sqlalchemy import Column, Integer, String, DateTime, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base


class Model(Base):
    """
    元模型定义表
    定义资源类型的元数据，包括属性结构、校验规则等
    """
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(100), unique=True, nullable=False, comment="模型名称")
    code = Column(String(50), unique=True, nullable=False, comment="模型代码")
    description = Column(String(500), comment="模型描述")
    category = Column(String(50), nullable=False, comment="资源分类")
    icon = Column(String(100), default="box", comment="图标")
    color = Column(String(20), default="#ccc", comment="颜色")
    is_active = Column(Boolean, default=True, comment="是否启用")
    unique_key_id = Column(UUID(as_uuid=True), nullable=True, comment="唯一标识属性ID")
    show_key_id = Column(UUID(as_uuid=True), nullable=True, comment="显示属性ID")
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
