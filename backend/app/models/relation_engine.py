import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum, func, Index, Integer, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class MappingType(str, enum.Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class RelationDefinitionStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class RelationDefinition(Base):
    """
    关系定义表 - 定义元模型之间的关系
    与现有 ModelRelation 解耦，提供更完整的关系引擎能力
    """
    __tablename__ = "relation_definitions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    name = Column(String(100), nullable=False, comment="关系名称")
    code = Column(String(50), unique=True, nullable=False, comment="关系编码")
    description = Column(String(500), nullable=True, comment="关系描述")
    
    source_model_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("models.id", ondelete="CASCADE"), 
        nullable=False,
        comment="源模型ID(子资源)"
    )
    target_model_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("models.id", ondelete="CASCADE"), 
        nullable=False,
        comment="目标模型ID(父资源)"
    )
    
    mapping_type = Column(
        SQLEnum(MappingType, name='mappingtype', create_constraint=False, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=MappingType.ONE_TO_MANY,
        comment="映射类型: one_to_one/one_to_many/many_to_one/many_to_many"
    )
    
    relation_label = Column(String(100), nullable=False, comment="关系显示名(如: 包含)")
    inverse_label = Column(String(100), nullable=True, comment="反向关系显示名(如: 属于)")
    
    is_hierarchical = Column(Boolean, default=True, comment="是否层级关系(用于层级视图)")
    is_bidirectional = Column(Boolean, default=False, comment="是否双向关系")
    
    min_cardinality = Column(Integer, default=0, comment="最小基数")
    max_cardinality = Column(Integer, default=-1, comment="最大基数(-1表示无限)")
    
    status = Column(
        SQLEnum(RelationDefinitionStatus, name='relationdefinitionstatus', create_constraint=False, native_enum=False, values_callable=lambda obj: [e.value for e in obj]),
        default=RelationDefinitionStatus.DRAFT,
        comment="状态: draft/active/inactive"
    )
    
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    source_model = relationship("ModelV2", foreign_keys=[source_model_id], back_populates="source_relation_definitions")
    target_model = relationship("ModelV2", foreign_keys=[target_model_id], back_populates="target_relation_definitions")
    instance_relations = relationship("InstanceRelation", back_populates="relation_definition", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_relation_definitions_source_model_id', 'source_model_id'),
        Index('ix_relation_definitions_target_model_id', 'target_model_id'),
        Index('ix_relation_definitions_status', 'status'),
        UniqueConstraint('source_model_id', 'target_model_id', 'code', name='uq_relation_definition'),
        CheckConstraint('source_model_id != target_model_id', name='no_self_relation_definition'),
    )


class InstanceRelation(Base):
    """
    实例关系表 - 维护实例之间的具体映射关系
    """
    __tablename__ = "instance_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    relation_definition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("relation_definitions.id", ondelete="CASCADE"),
        nullable=False,
        comment="关系定义ID"
    )
    
    source_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="源实例ID(子资源)"
    )
    
    target_instance_id = Column(
        UUID(as_uuid=True),
        ForeignKey("instances.id", ondelete="CASCADE"),
        nullable=False,
        comment="目标实例ID(父资源)"
    )
    
    attributes = Column(JSONB, default=dict, comment="关系属性: 如端口、带宽等")
    
    valid_from = Column(DateTime(timezone=True), nullable=True, comment="生效开始时间")
    valid_to = Column(DateTime(timezone=True), nullable=True, comment="生效结束时间")
    
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    relation_definition = relationship("RelationDefinition", back_populates="instance_relations")
    source_instance = relationship("Instance", foreign_keys=[source_instance_id], back_populates="outgoing_relations")
    target_instance = relationship("Instance", foreign_keys=[target_instance_id], back_populates="incoming_relations")
    
    __table_args__ = (
        Index('ix_instance_relations_relation_definition_id', 'relation_definition_id'),
        Index('ix_instance_relations_source_instance_id', 'source_instance_id'),
        Index('ix_instance_relations_target_instance_id', 'target_instance_id'),
        UniqueConstraint('relation_definition_id', 'source_instance_id', 'target_instance_id', name='uq_instance_relation'),
        CheckConstraint('source_instance_id != target_instance_id', name='no_self_instance_relation'),
    )
