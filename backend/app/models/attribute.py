from sqlalchemy import String, JSON, Text, ForeignKey, Enum as SQLEnum, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from typing import Optional, Dict, Any

from app.db.base_class import Base


class AttributeType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    ENUM = "enum"
    REFERENCE = "reference"  # 引用其他实例


class Attribute(Base):
    """
    属性定义表 - 定义模型可拥有的属性
    """
    
    model_id: Mapped[str] = mapped_column(ForeignKey("model.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    attribute_type: Mapped[AttributeType] = mapped_column(SQLEnum(AttributeType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 校验规则
    is_required: Mapped[bool] = mapped_column(default=False)
    is_unique: Mapped[bool] = mapped_column(default=False)
    default_value: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    
    # 类型特定配置
    # STRING: {"max_length": 255, "min_length": 0, "regex": ""}
    # INTEGER/FLOAT: {"min": 0, "max": 100}
    # ENUM: {"options": ["a", "b", "c"]}
    # REFERENCE: {"target_model": "model_id"}
    validation_rules: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    
    # 排序
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    
    # 是否可编辑
    is_editable: Mapped[bool] = mapped_column(default=True)
    is_visible: Mapped[bool] = mapped_column(default=True)
    
    # 关系
    model: Mapped["Model"] = relationship("Model", back_populates="attributes")
