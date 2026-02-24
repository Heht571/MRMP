import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLEnum, func, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


# DEPRECATED: This module is deprecated and will be removed in future versions.
# Please use app.models.relation_engine instead.


class RelationType(str, enum.Enum):
    CONTAIN = "contain"
    CONNECT = "connect"
    CARRY = "carry"
    ASSOCIATE = "associate"
    BELONGS_TO_REGION = "belongs_to_region"
    PARENT_CHILD = "parent_child"
    UPSTREAM_DOWNSTREAM = "upstream_downstream"
    PRIMARY_BACKUP = "primary_backup"


class Relation(Base):
    """
    资源关系表 - 维护资源间的拓扑关系
    支持: contain(包含), connect(连接), carry(承载), associate(关联)等
    """
    __tablename__ = "relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    source_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("instances.id", ondelete="CASCADE"), 
        nullable=False,
        comment="源实例ID"
    )
    
    target_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("instances.id", ondelete="CASCADE"), 
        nullable=False,
        comment="目标实例ID"
    )
    
    relation_type = Column(
        SQLEnum(RelationType), 
        nullable=False,
        comment="关系类型: contain/connect/carry/associate等"
    )
    
    attributes = Column(JSONB, default=dict, comment="关系属性: 如连接端口、带宽等")
    
    description = Column(String(500), nullable=True, comment="关系描述")
    
    is_bidirectional = Column(String(10), default="false", comment="是否双向关系")
    weight = Column(String(10), default="1", comment="关系权重")
    
    valid_from = Column(DateTime(timezone=True), nullable=True, comment="生效开始时间")
    valid_to = Column(DateTime(timezone=True), nullable=True, comment="生效结束时间")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    source = relationship(
        "Instance", 
        foreign_keys=[source_id]
    )
    target = relationship(
        "Instance", 
        foreign_keys=[target_id]
    )
    
    __table_args__ = (
        Index('ix_relations_source_id', 'source_id'),
        Index('ix_relations_target_id', 'target_id'),
        Index('ix_relations_relation_type', 'relation_type'),
        Index('ix_relations_source_target', 'source_id', 'target_id'),
        CheckConstraint('source_id != target_id', name='no_self_relation'),
    )
    
    def __repr__(self):
        return f"<Relation {self.source_id} -> {self.target_id} ({self.relation_type.value})>"
    
    def get_attribute(self, key: str, default=None):
        """获取关系属性值"""
        return self.attributes.get(key, default) if self.attributes else default
    
    def set_attribute(self, key: str, value):
        """设置关系属性值"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value
