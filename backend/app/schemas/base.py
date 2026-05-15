from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class RegionLevel(str, Enum):
    PROVINCE = "province"
    CITY = "city"
    DISTRICT = "district"
    PLANNING_AREA = "planning_area"


class AreaType(str, Enum):
    IMPORTANT_AGG = "IMPORTANT_AGG"
    INTEGRATED_SERVICE = "INTEGRATED_SERVICE"
    RURAL_HOTSPOT = "RURAL_HOTSPOT"


class InstanceStatus(str, Enum):
    PLANNING = "planning"
    CONSTRUCTION = "construction"
    ACTIVE = "active"
    RETIRED = "retired"


class EvolutionType(str, Enum):
    TARGET = "TARGET"
    ANCHOR = "ANCHOR"


class MilestoneStatus(str, Enum):
    PENDING = "PENDING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class MilestonePhase(str, Enum):
    INITIATION = "initiation"
    PROCUREMENT = "procurement"
    DESIGN = "design"
    CONSTRUCTION = "construction"
    FACILITY = "facility"
    COMPLETION = "completion"


class MilestoneKey(str, Enum):
    PROJECT_APPROVAL = "project_approval"
    PROCUREMENT_DECISION = "procurement_decision"
    RECEIPT = "receipt"
    CERTIFICATE = "certificate"
    DESIGN_SURVEY = "design_survey"
    DESIGN_APPROVAL = "design_approval"
    MATERIALS_ARRIVAL = "materials_arrival"
    CONSTRUCTION = "construction"
    EXTERNAL_POWER = "external_power"
    DECORATION = "decoration"
    EQUIPMENT_INSTALL = "equipment_install"
    PIPELINE = "pipeline"
    CIRCUIT = "circuit"
    COMPLETION = "completion"
    GO_LIVE = "go_live"


class RelationType(str, Enum):
    CONTAIN = "contain"
    CONNECT = "connect"
    CARRY = "carry"
    ASSOCIATE = "associate"
    BELONGS_TO_REGION = "belongs_to_region"
    PARENT = "parent"
    BACKUP = "backup"


class AttributeType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    ENUM = "enum"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"


class RegionBase(BaseModel):
    name: str = Field(..., max_length=100, description="区域名称")
    code: str = Field(..., max_length=50, description="区域编码")
    level: RegionLevel = Field(..., description="区域层级")
    parent_id: Optional[UUID] = Field(None, description="父级区域ID")
    area_type: Optional[AreaType] = Field(None, description="区域类型(仅规划区)")
    description: Optional[str] = Field(None, max_length=500, description="区域描述")
    planned_room_count: Optional[int] = Field(0, ge=0, description="规划机房数量")


class RegionCreate(RegionBase):
    pass


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    code: Optional[str] = Field(None, max_length=50)
    area_type: Optional[AreaType] = None
    description: Optional[str] = Field(None, max_length=500)
    planned_room_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class RegionResponse(RegionBase):
    id: UUID
    actual_room_count: int = Field(0, description="实际机房数量")
    is_active: bool
    full_path: Optional[str] = None
    area_type_display: Optional[str] = None
    expected_room_count: int = Field(0, description="期望机房数量")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RegionTreeResponse(RegionResponse):
    children: List["RegionTreeResponse"] = Field(default_factory=list)


class AttributeBase(BaseModel):
    name: str = Field(..., max_length=100, description="属性名称(英文键)")
    label: str = Field(..., max_length=100, description="属性标签(中文)")
    description: Optional[str] = Field(None, max_length=500, description="属性描述")
    type: AttributeType = Field(AttributeType.STRING, description="数据类型")
    is_required: bool = Field(False, description="是否必填")
    is_unique: bool = Field(False, description="是否唯一")
    is_indexed: bool = Field(False, description="是否索引")
    is_readonly: bool = Field(False, description="是否只读")
    default_value: Optional[str] = Field(None, description="默认值")
    enum_values: Optional[List[Any]] = Field(None, description="枚举值列表(支持字符串或对象)")
    validation_regex: Optional[str] = Field(None, max_length=500, description="正则校验规则")
    min_value: Optional[str] = Field(None, max_length=50, description="最小值")
    max_value: Optional[str] = Field(None, max_length=50, description="最大值")
    sort_order: int = Field(0, description="排序序号")
    group_name: Optional[str] = Field(None, max_length=50, description="属性分组名称")


class AttributeCreate(AttributeBase):
    pass


class ModelAttributeRef(BaseModel):
    attribute_id: Optional[UUID] = Field(None, description="全局属性ID")
    name: str = Field(..., max_length=100, description="属性名称(英文键)")
    label: str = Field(..., max_length=100, description="属性标签(中文)")
    description: Optional[str] = Field(None, max_length=500, description="属性描述")
    type: AttributeType = Field(AttributeType.STRING, description="数据类型")
    is_required: bool = Field(False, description="是否必填")
    is_unique: bool = Field(False, description="是否唯一")
    is_indexed: bool = Field(False, description="是否索引")
    is_readonly: bool = Field(False, description="是否只读")
    default_value: Optional[str] = Field(None, description="默认值")
    enum_values: Optional[List[str]] = Field(None, description="枚举值列表")
    sort_order: int = Field(0, description="排序序号")


class AttributeUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_required: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_indexed: Optional[bool] = None
    default_value: Optional[str] = None
    enum_values: Optional[List[str]] = None
    sort_order: Optional[int] = None


class AttributeResponse(AttributeBase):
    id: UUID
    model_id: UUID
    updated_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelBase(BaseModel):
    name: str = Field(..., max_length=100, description="模型名称")
    code: str = Field(..., max_length=50, description="模型代码")
    description: Optional[str] = Field(None, max_length=500, description="模型描述")
    category: str = Field(..., max_length=50, description="模型分类")
    icon: Optional[str] = Field(None, max_length=100, description="图标标识")
    color: Optional[str] = Field(None, max_length=20, description="显示颜色")


class ModelCreate(ModelBase):
    attributes: List[AttributeCreate] = Field(default_factory=list, description="属性列表")


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    attributes: Optional[List[ModelAttributeRef]] = Field(None, description="属性列表(更新时替换全部属性)")
    relations: Optional[List[Dict[str, Any]]] = Field(None, description="关联关系列表")


class ModelResponse(ModelBase):
    id: UUID
    is_active: bool
    is_system: bool
    attributes: List[AttributeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InstanceBase(BaseModel):
    model_id: UUID = Field(..., description="关联模型ID")
    name: str = Field(..., max_length=200, description="实例名称")
    code: Optional[str] = Field(None, max_length=100, description="实例编码")
    status: InstanceStatus = Field(default=InstanceStatus.PLANNING, description="生命周期状态")
    data: Dict[str, Any] = Field(default_factory=dict, description="动态属性数据")


class InstanceCreate(InstanceBase):
    @field_validator("data")
    @classmethod
    def validate_data(cls, v):
        return v or {}


class InstanceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    code: Optional[str] = Field(None, max_length=100)
    status: Optional[InstanceStatus] = None
    data: Optional[Dict[str, Any]] = None
    version: Optional[int] = Field(None, description="乐观锁版本号")


class InstanceResponse(InstanceBase):
    id: UUID
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InstanceDetailResponse(InstanceResponse):
    model: Optional[ModelResponse] = None


class LifecycleMilestoneBase(BaseModel):
    instance_id: UUID = Field(..., description="关联实例ID")
    milestone_key: MilestoneKey = Field(..., description="里程碑类型")
    phase: MilestonePhase = Field(..., description="建设阶段")
    milestone_name: str = Field(..., max_length=100, description="里程碑名称")
    description: Optional[str] = Field(None, max_length=500, description="里程碑描述")
    planned_start_date: Optional[date] = Field(None, description="计划开始日期")
    planned_end_date: Optional[date] = Field(None, description="计划结束日期")
    actual_start_date: Optional[date] = Field(None, description="实际开始日期")
    actual_end_date: Optional[date] = Field(None, description="实际结束日期")
    duration_days: int = Field(0, ge=0, description="持续时间(天)")
    status: MilestoneStatus = Field(MilestoneStatus.PENDING, description="状态")
    progress: int = Field(0, ge=0, le=100, description="进度百分比")
    responsible_person: Optional[str] = Field(None, max_length=100, description="负责人")
    responsible_dept: Optional[str] = Field(None, max_length=100, description="责任部门")
    remarks: Optional[str] = Field(None, max_length=500, description="备注")


class LifecycleMilestoneCreate(LifecycleMilestoneBase):
    pass


class LifecycleMilestoneUpdate(BaseModel):
    planned_start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    status: Optional[MilestoneStatus] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    responsible_person: Optional[str] = None
    responsible_dept: Optional[str] = None
    remarks: Optional[str] = None


class LifecycleMilestoneResponse(LifecycleMilestoneBase):
    id: UUID
    sort_order: int
    is_critical_path: bool
    dependencies: Optional[str] = None
    is_delayed: bool = False
    delay_days: int = 0
    phase_display: str = ""
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RelationBase(BaseModel):
    source_id: UUID = Field(..., description="源实例ID")
    target_id: UUID = Field(..., description="目标实例ID")
    relation_type: RelationType = Field(..., description="关系类型")
    attributes: Optional[Dict[str, Any]] = Field(None, description="关系属性")


class RelationCreate(RelationBase):
    @field_validator("source_id")
    @classmethod
    def validate_source_not_equal_target(cls, v, info):
        if "target_id" in info.data and v == info.data["target_id"]:
            raise ValueError("源实例和目标实例不能相同")
        return v


class RelationUpdate(BaseModel):
    relation_type: Optional[RelationType] = None
    attributes: Optional[Dict[str, Any]] = None


class RelationResponse(RelationBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    total: int = Field(..., description="总记录数")
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页记录数")
    items: List[Any] = Field(default_factory=list, description="数据列表")


class StatisticsResponse(BaseModel):
    total_rooms: int = Field(0, description="机房总数")
    target_rooms: int = Field(0, description="目标机房数")
    anchor_rooms: int = Field(0, description="锚点机房数")
    by_status: Dict[str, int] = Field(default_factory=dict, description="按状态统计")
    by_area_type: Dict[str, int] = Field(default_factory=dict, description="按区域类型统计")
    by_city: Dict[str, int] = Field(default_factory=dict, description="按地市统计")
    construction_progress: Dict[str, Any] = Field(default_factory=dict, description="建设进度统计")


RegionTreeResponse.model_rebuild()
