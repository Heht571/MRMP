import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Enum as SQLEnum, func, Index, Integer, UniqueConstraint
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
    TIMESERIES = "timeseries"


class TriggerEventType(str, enum.Enum):
    BEFORE_CREATE = "before_create"
    AFTER_CREATE = "after_create"
    BEFORE_UPDATE = "before_update"
    AFTER_UPDATE = "after_update"
    BEFORE_DELETE = "before_delete"
    AFTER_DELETE = "after_delete"


class TriggerActionType(str, enum.Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    SCRIPT = "script"


class OperateType(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class GlobalAttribute(Base):
    """全局属性池 - 属性全局定义，可被多个模型复用"""
    __tablename__ = "global_attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, comment="属性名称(英文键，全局唯一)")
    label = Column(String(100), nullable=False, comment="属性标签(中文显示名)")
    description = Column(String(500), nullable=True, comment="属性描述")
    
    type = Column(SQLEnum(AttributeType, name='attributetype_v2', create_constraint=False, native_enum=False, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AttributeType.STRING, comment="数据类型")
    
    is_choice = Column(Boolean, default=False, comment="是否枚举类型")
    is_list = Column(Boolean, default=False, comment="是否列表类型")
    is_unique = Column(Boolean, default=False, comment="是否唯一")
    is_indexed = Column(Boolean, default=False, comment="是否索引")
    is_sortable = Column(Boolean, default=False, comment="是否可排序")
    
    default_value = Column(Text, nullable=True, comment="默认值")
    enum_values = Column(JSONB, nullable=True, comment="枚举值列表")
    validation_regex = Column(String(500), nullable=True, comment="正则校验规则")
    
    min_value = Column(String(50), nullable=True, comment="最小值")
    max_value = Column(String(50), nullable=True, comment="最大值")
    
    is_reference = Column(Boolean, default=False, comment="是否引用属性")
    reference_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id"), nullable=True, comment="引用的模型ID")
    
    is_computed = Column(Boolean, default=False, comment="是否计算属性")
    compute_expr = Column(Text, nullable=True, comment="计算表达式")
    compute_script = Column(Text, nullable=True, comment="计算脚本")
    
    choice_webhook = Column(JSONB, nullable=True, comment="枚举值Webhook配置")
    choice_script = Column(Text, nullable=True, comment="枚举值计算脚本")

    is_timeseries = Column(Boolean, default=False, comment="是否时序属性")
    timeseries_unit = Column(String(50), nullable=True, comment="时序单位: cpu/memory/disk/network/custom")
    timeseries_interval = Column(Integer, default=60, comment="采样间隔(秒)")
    timeseries_retention = Column(Integer, default=30, comment="数据保留天数")
    timeseries_aggregation = Column(String(20), default='avg', comment="默认聚合函数: avg/min/max/sum/last")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    reference_model = relationship("ModelV2", foreign_keys=[reference_model_id])
    model_attributes = relationship("ModelAttribute", back_populates="attribute", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_global_attributes_name', 'name'),
        Index('ix_global_attributes_type', 'type'),
    )


class ModelRelation(Base):
    """
    [DEPRECATED] 模型关联关系定义
    Please use app.models.relation_engine.RelationDefinition instead.
    """
    __tablename__ = "model_relations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, comment="源模型ID(被包含方)")
    target_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, comment="目标模型ID(包含方)")
    configured_by_model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, comment="配置此关系的模型ID")
    
    relation_type = Column(String(50), nullable=False, comment="关系类型: contain/connect")
    relation_name = Column(String(100), nullable=False, comment="关系名称(中文)")
    inverse_name = Column(String(100), nullable=True, comment="反向关系名称")
    
    description = Column(String(500), nullable=True, comment="关系描述")
    
    min_cardinality = Column(Integer, default=0, comment="最小基数")
    max_cardinality = Column(Integer, default=-1, comment="最大基数(-1表示无限)")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    source_model = relationship("ModelV2", foreign_keys=[source_model_id], back_populates="outgoing_relations")
    target_model = relationship("ModelV2", foreign_keys=[target_model_id], back_populates="incoming_relations")
    configured_by_model = relationship("ModelV2", foreign_keys=[configured_by_model_id])
    
    __table_args__ = (
        Index('ix_model_relations_source_model_id', 'source_model_id'),
        Index('ix_model_relations_target_model_id', 'target_model_id'),
        Index('ix_model_relations_configured_by_model_id', 'configured_by_model_id'),
        UniqueConstraint('source_model_id', 'target_model_id', 'relation_type', name='uq_model_relation'),
    )


class ModelV2(Base):
    """元模型定义表 - 扩展版本"""
    __tablename__ = "models"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="模型名称(中文)")
    code = Column(String(50), unique=True, nullable=False, comment="模型代码(英文)")
    description = Column(String(500), nullable=True, comment="模型描述")
    
    category = Column(String(50), nullable=False, comment="模型分类")
    icon = Column(String(100), nullable=True, comment="图标标识")
    color = Column(String(20), nullable=True, comment="显示颜色")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_root_model = Column(Boolean, default=False, comment="是否为根节点模型(顶级资源)")

    unique_key_id = Column(UUID(as_uuid=True), ForeignKey("global_attributes.id"), nullable=True, comment="唯一标识属性ID")
    show_key_id = Column(UUID(as_uuid=True), ForeignKey("global_attributes.id"), nullable=True, comment="显示名称属性ID")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    unique_key = relationship("GlobalAttribute", foreign_keys=[unique_key_id])
    show_key = relationship("GlobalAttribute", foreign_keys=[show_key_id])
    model_attributes = relationship("ModelAttribute", back_populates="model", cascade="all, delete-orphan")
    instances = relationship("Instance", back_populates="model")
    parent_inheritances = relationship("ModelInheritance", foreign_keys="ModelInheritance.child_id", back_populates="child")
    child_inheritances = relationship("ModelInheritance", foreign_keys="ModelInheritance.parent_id", back_populates="parent")
    unique_constraints = relationship("ModelUniqueConstraint", back_populates="model", cascade="all, delete-orphan")
    triggers = relationship("ModelTrigger", back_populates="model", cascade="all, delete-orphan")
    outgoing_relations = relationship("ModelRelation", foreign_keys="ModelRelation.source_model_id", back_populates="source_model", cascade="all, delete-orphan")
    incoming_relations = relationship("ModelRelation", foreign_keys="ModelRelation.target_model_id", back_populates="target_model")
    
    # New Relation Engine Relationships
    source_relation_definitions = relationship("RelationDefinition", foreign_keys="RelationDefinition.source_model_id", back_populates="source_model", cascade="all, delete-orphan")
    target_relation_definitions = relationship("RelationDefinition", foreign_keys="RelationDefinition.target_model_id", back_populates="target_model")


Model = ModelV2


class ModelAttribute(Base):
    """模型-属性关联表 - 定义属性在特定模型中的配置"""
    __tablename__ = "model_attributes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("global_attributes.id", ondelete="CASCADE"), nullable=False)
    
    is_required = Column(Boolean, default=False, comment="是否必填")
    is_readonly = Column(Boolean, default=False, comment="是否只读")
    default_show = Column(Boolean, default=True, comment="是否默认显示")
    
    sort_order = Column(Integer, default=0, comment="排序序号")
    group_name = Column(String(50), nullable=True, comment="属性分组名称")
    
    override_label = Column(String(100), nullable=True, comment="覆盖显示标签")
    override_default = Column(Text, nullable=True, comment="覆盖默认值")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    model = relationship("ModelV2", back_populates="model_attributes")
    attribute = relationship("GlobalAttribute", back_populates="model_attributes")
    
    __table_args__ = (
        Index('ix_model_attributes_model_id', 'model_id'),
        UniqueConstraint('model_id', 'attribute_id', name='uq_model_attribute'),
    )


class ModelInheritance(Base):
    """模型继承关系表 - 支持选择性继承属性"""
    __tablename__ = "model_inheritance"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    attribute_id = Column(UUID(as_uuid=True), ForeignKey("global_attributes.id", ondelete="CASCADE"), nullable=True, comment="继承的属性ID，为空表示继承全部")
    sort_order = Column(Integer, default=0, comment="继承优先级")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    parent = relationship("ModelV2", foreign_keys=[parent_id], back_populates="child_inheritances")
    child = relationship("ModelV2", foreign_keys=[child_id], back_populates="parent_inheritances")
    attribute = relationship("GlobalAttribute")
    
    __table_args__ = (
        UniqueConstraint('parent_id', 'child_id', 'attribute_id', name='uq_model_inheritance_attr'),
    )


class ModelUniqueConstraint(Base):
    """模型唯一约束表 - 支持多属性组合唯一"""
    __tablename__ = "model_unique_constraints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="约束名称")
    description = Column(String(500), nullable=True, comment="约束描述")
    attribute_ids = Column(JSONB, nullable=False, comment="参与约束的属性ID列表")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    model = relationship("ModelV2", back_populates="unique_constraints")
    
    __table_args__ = (
        Index('ix_model_unique_constraints_model_id', 'model_id'),
    )


class ModelTrigger(Base):
    """模型触发器表"""
    __tablename__ = "model_triggers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="触发器名称")
    description = Column(String(500), nullable=True, comment="触发器描述")
    
    event_type = Column(SQLEnum(TriggerEventType), nullable=False, comment="触发事件类型")
    action_type = Column(SQLEnum(TriggerActionType), nullable=False, comment="动作类型")
    
    condition = Column(JSONB, nullable=True, comment="触发条件")
    action_config = Column(JSONB, nullable=False, comment="动作配置")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True, comment="创建人")
    
    model = relationship("ModelV2", back_populates="triggers")
    
    __table_args__ = (
        Index('ix_model_triggers_model_id', 'model_id'),
    )


class OperationRecord(Base):
    """操作记录表"""
    __tablename__ = "operation_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operate_type = Column(SQLEnum(OperateType), nullable=False, comment="操作类型")
    model_id = Column(UUID(as_uuid=True), nullable=True, comment="模型ID")
    instance_id = Column(UUID(as_uuid=True), nullable=True, comment="实例ID")
    
    origin = Column(String(50), nullable=True, comment="来源")
    ticket_id = Column(String(100), nullable=True, comment="工单ID")
    reason = Column(Text, nullable=True, comment="原因")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True, comment="操作人")
    
    attribute_histories = relationship("AttributeHistory", back_populates="record", cascade="all, delete-orphan")
    relation_histories = relationship("RelationHistory", back_populates="record", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_operation_records_model_id', 'model_id'),
        Index('ix_operation_records_instance_id', 'instance_id'),
        Index('ix_operation_records_created_at', 'created_at'),
        Index('ix_operation_records_created_by', 'created_by'),
    )


class AttributeHistory(Base):
    """属性变更历史表"""
    __tablename__ = "attribute_histories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("operation_records.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(UUID(as_uuid=True), nullable=False, comment="实例ID")
    attribute_id = Column(UUID(as_uuid=True), nullable=True, comment="属性ID")
    attribute_name = Column(String(100), nullable=False, comment="属性名称")
    
    old_value = Column(Text, nullable=True, comment="旧值")
    new_value = Column(Text, nullable=True, comment="新值")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    record = relationship("OperationRecord", back_populates="attribute_histories")
    
    __table_args__ = (
        Index('ix_attribute_histories_instance_id', 'instance_id'),
        Index('ix_attribute_histories_attribute_id', 'attribute_id'),
    )


class RelationHistory(Base):
    """关系变更历史表"""
    __tablename__ = "relation_histories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("operation_records.id", ondelete="CASCADE"), nullable=False)
    relation_id = Column(UUID(as_uuid=True), nullable=True, comment="关系ID")
    source_id = Column(UUID(as_uuid=True), nullable=False, comment="源实例ID")
    target_id = Column(UUID(as_uuid=True), nullable=False, comment="目标实例ID")
    relation_type = Column(String(50), nullable=False, comment="关系类型")
    
    old_value = Column(JSONB, nullable=True, comment="旧值")
    new_value = Column(JSONB, nullable=True, comment="新值")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    record = relationship("OperationRecord", back_populates="relation_histories")
    
    __table_args__ = (
        Index('ix_relation_histories_source_id', 'source_id'),
        Index('ix_relation_histories_target_id', 'target_id'),
    )


class TriggerHistory(Base):
    """触发器执行历史表"""
    __tablename__ = "trigger_histories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_id = Column(UUID(as_uuid=True), ForeignKey("model_triggers.id", ondelete="CASCADE"), nullable=False)
    instance_id = Column(UUID(as_uuid=True), nullable=False, comment="实例ID")
    
    is_success = Column(Boolean, default=False, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误信息")
    response_data = Column(JSONB, nullable=True, comment="响应数据")
    
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('ix_trigger_histories_trigger_id', 'trigger_id'),
        Index('ix_trigger_histories_instance_id', 'instance_id'),
    )
