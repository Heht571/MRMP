import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, func, Index, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class Instance(Base):
    """
    资源实例表 - 所有资源的统一存储
    所有属性存储在 data JSONB 字段中，由元模型定义结构
    """
    __tablename__ = "instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=False, comment="关联模型ID")
    
    name = Column(String(200), nullable=False, comment="实例名称")
    code = Column(String(100), nullable=True, comment="实例编码")
    
    # 核心字段增强：生命周期与并发控制
    status = Column(String(50), default="planning", nullable=False, comment="生命周期状态")
    version = Column(Integer, default=1, nullable=False, comment="乐观锁版本号")
    
    data = Column(JSONB, default=dict, comment="动态属性数据(JSONB)")
    
    description = Column(Text, nullable=True, comment="实例描述")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    updated_by = Column(String(100), nullable=True, comment="更新人")
    
    model = relationship("ModelV2", back_populates="instances")
    
    # 关系引擎反向引用
    outgoing_relations = relationship("InstanceRelation", foreign_keys="InstanceRelation.source_instance_id", back_populates="source_instance", cascade="all, delete-orphan")
    incoming_relations = relationship("InstanceRelation", foreign_keys="InstanceRelation.target_instance_id", back_populates="target_instance", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_instances_model_id', 'model_id'),
        Index('ix_instances_data_gin', 'data', postgresql_using='gin'),
        Index('ix_instances_name', 'name'),
        Index('ix_instances_code', 'code'),
        Index('ix_instances_status', 'status'),
        Index('ix_instances_created_at', 'created_at'),
        Index('ix_instances_model_id_status', 'model_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Instance {self.name}>"
    
    def get_attribute(self, key: str, default=None):
        """获取动态属性值"""
        return self.data.get(key, default) if self.data else default
    
    def set_attribute(self, key: str, value):
        """设置动态属性值"""
        if self.data is None:
            self.data = {}
        self.data[key] = value
    
    def to_dict(self):
        """转换为字典，包含动态属性"""
        result = {
            "id": str(self.id),
            "name": self.name,
            "code": self.code,
            "model_id": str(self.model_id),
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if self.data:
            result.update(self.data)
        return result
