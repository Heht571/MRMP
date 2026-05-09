from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, computed_field
from enum import Enum


class RelationType(str, Enum):
    CONTAIN = "contain"   # 包含关系，有层级，父→子
    CONNECT = "connect"   # 连接关系，双向对等


class MappingType(str, Enum):
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class RelationDefinitionStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"


class RelationDefinitionBase(BaseModel):
    name: str = Field(..., max_length=100, description="关系名称")
    code: str = Field(..., max_length=50, description="关系编码")
    description: Optional[str] = Field(None, max_length=500, description="关系描述")
    source_model_id: UUID = Field(..., description="源模型ID")
    target_model_id: UUID = Field(..., description="目标模型ID")
    relation_type: RelationType = Field(RelationType.CONTAIN, description="关系类型: contain=包含(层级), connect=连接(对等)")
    mapping_type: MappingType = Field(MappingType.ONE_TO_MANY, description="映射类型")
    min_cardinality: int = Field(0, description="最小基数")
    max_cardinality: int = Field(-1, description="最大基数(-1表示无限)")
    sort_order: int = Field(0, description="排序序号")


class RelationDefinitionCreate(RelationDefinitionBase):
    pass


class RelationDefinitionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    relation_type: Optional[RelationType] = None
    mapping_type: Optional[MappingType] = None
    min_cardinality: Optional[int] = None
    max_cardinality: Optional[int] = None
    status: Optional[RelationDefinitionStatus] = None
    sort_order: Optional[int] = None


class ModelBrief(BaseModel):
    id: UUID
    name: str
    code: str
    category: str
    
    class Config:
        from_attributes = True


class RelationDefinitionResponse(RelationDefinitionBase):
    id: UUID
    status: RelationDefinitionStatus
    source_model: Optional[ModelBrief] = None
    target_model: Optional[ModelBrief] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    @computed_field
    def relation_label(self) -> str:
        return "包含" if self.relation_type == RelationType.CONTAIN else "连接"

    @computed_field
    def inverse_label(self) -> str:
        return "被包含" if self.relation_type == RelationType.CONTAIN else "连接于"

    @computed_field
    def is_hierarchical(self) -> bool:
        return self.relation_type == RelationType.CONTAIN

    @computed_field
    def is_bidirectional(self) -> bool:
        return self.relation_type == RelationType.CONNECT

    class Config:
        from_attributes = True


class InstanceRelationBase(BaseModel):
    relation_definition_id: UUID = Field(..., description="关系定义ID")
    source_instance_id: UUID = Field(..., description="源实例ID(子资源)")
    target_instance_id: UUID = Field(..., description="目标实例ID(父资源)")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="关系属性")
    valid_from: Optional[datetime] = Field(None, description="生效开始时间")
    valid_to: Optional[datetime] = Field(None, description="生效结束时间")
    sort_order: int = Field(0, description="排序序号")


class InstanceRelationCreate(InstanceRelationBase):
    pass


class InstanceRelationBatchCreate(BaseModel):
    relation_definition_id: UUID = Field(..., description="关系定义ID")
    relations: List[InstanceRelationCreate] = Field(..., description="关系列表")


class InstanceRelationUpdate(BaseModel):
    attributes: Optional[Dict[str, Any]] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    sort_order: Optional[int] = None


class InstanceBrief(BaseModel):
    id: UUID
    name: str
    code: Optional[str] = None
    model_id: UUID
    model_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class InstanceRelationResponse(InstanceRelationBase):
    id: UUID
    source_instance: Optional[InstanceBrief] = None
    target_instance: Optional[InstanceBrief] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class HierarchyNode(BaseModel):
    id: UUID
    name: str
    code: Optional[str] = None
    model_id: UUID
    model_name: str
    model_code: str
    model_color: Optional[str] = None
    model_icon: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    children: List["HierarchyNode"] = Field(default_factory=list)
    relation_name: Optional[str] = None
    
    class Config:
        from_attributes = True


HierarchyNode.model_rebuild()


class HierarchyTreeResponse(BaseModel):
    root_model_id: UUID
    root_model_name: str
    nodes: List[HierarchyNode]
    total_count: int
