import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum, func, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class AttributeType(str, enum.Enum):
    STRING = "string"
    NUMBER = "number"
    ENUM = "enum"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"


class Model(Base):
    """
    元模型定义表 - 定义资源类型的元数据
    例如：机房、机柜、OLT、交换机等资源类型
    """
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="模型名称(中文)")
    code = Column(String(50), unique=True, nullable=False, comment="模型代码(英文)")
    description = Column(String(500), nullable=True, comment="模型描述")
    
    category = Column(String(50), nullable=False, comment="模型分类: room/cabinet/device/port/fiber等")
    icon = Column(String(100), nullable=True, comment="图标标识")
    color = Column(String(20), nullable=True, comment="显示颜色")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_system = Column(Boolean, default=False, comment="是否系统内置模型")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    attributes = relationship("Attribute", back_populates="model", cascade="all, delete-orphan")
    instances = relationship("Instance", back_populates="model")
    
    def __repr__(self):
        return f"<Model {self.name} ({self.code})>"


class Attribute(Base):
    """
    属性定义表 - 定义模型的字段结构
    所有属性值存储在 instances.data JSONB 字段中
    """
    __tablename__ = "attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    
    name = Column(String(100), nullable=False, comment="属性名称(英文键)")
    label = Column(String(100), nullable=False, comment="属性标签(中文显示名)")
    description = Column(String(500), nullable=True, comment="属性描述")
    
    type = Column(SQLEnum(AttributeType), nullable=False, default=AttributeType.STRING, comment="数据类型")
    is_required = Column(Boolean, default=False, comment="是否必填")
    is_unique = Column(Boolean, default=False, comment="是否唯一")
    is_indexed = Column(Boolean, default=False, comment="是否索引")
    is_readonly = Column(Boolean, default=False, comment="是否只读")
    
    default_value = Column(Text, nullable=True, comment="默认值")
    enum_values = Column(JSONB, nullable=True, comment="枚举值列表: ['value1', 'value2']")
    validation_regex = Column(String(500), nullable=True, comment="正则校验规则")
    
    min_value = Column(String(50), nullable=True, comment="最小值(数字/日期)")
    max_value = Column(String(50), nullable=True, comment="最大值(数字/日期)")
    
    sort_order = Column(String(10), default="0", comment="排序序号")
    group_name = Column(String(50), nullable=True, comment="属性分组名称")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    model = relationship("Model", back_populates="attributes")
    
    __table_args__ = (
        Index('ix_attributes_model_name', 'model_id', 'name'),
    )
    
    def __repr__(self):
        return f"<Attribute {self.name} ({self.type.value})>"
