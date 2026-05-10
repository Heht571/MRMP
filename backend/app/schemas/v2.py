from datetime import datetime, date
from typing import Optional, List, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class AttributeType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    ENUM = "enum"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    TIMESERIES = "timeseries"


class OperateType(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class EnumValueItem(BaseModel):
    value: str = Field(..., description="枚举值")
    label: str = Field(..., description="显示标签")
    color: Optional[str] = Field(None, description="颜色标识")
    description: Optional[str] = Field(None, description="描述")


class GlobalAttributeBase(BaseModel):
    name: str = Field(..., max_length=100, description="属性名称(英文键)")
    label: str = Field(..., max_length=100, description="属性标签(中文)")
    description: Optional[str] = Field(None, max_length=500, description="属性描述")
    type: AttributeType = Field(AttributeType.STRING, description="数据类型")
    
    is_choice: bool = Field(False, description="是否枚举类型")
    is_list: bool = Field(False, description="是否列表类型")
    is_unique: bool = Field(False, description="是否唯一")
    is_indexed: bool = Field(False, description="是否索引")
    is_sortable: bool = Field(False, description="是否可排序")
    
    default_value: Optional[str] = Field(None, description="默认值")
    enum_values: Optional[List[EnumValueItem]] = Field(None, description="枚举值列表")
    validation_regex: Optional[str] = Field(None, description="正则校验规则")
    
    min_value: Optional[str] = Field(None, description="最小值")
    max_value: Optional[str] = Field(None, description="最大值")
    
    is_reference: bool = Field(False, description="是否引用属性")
    reference_model_id: Optional[UUID] = Field(None, description="引用的模型ID")
    
    is_computed: bool = Field(False, description="是否计算属性")
    compute_expr: Optional[str] = Field(None, description="计算表达式")
    compute_script: Optional[str] = Field(None, description="计算脚本")
    
    choice_webhook: Optional[Dict[str, Any]] = Field(None, description="枚举值Webhook配置")
    choice_script: Optional[str] = Field(None, description="枚举值计算脚本")


class GlobalAttributeCreate(GlobalAttributeBase):
    pass


class GlobalAttributeUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_choice: Optional[bool] = None
    is_list: Optional[bool] = None
    is_unique: Optional[bool] = None
    is_indexed: Optional[bool] = None
    is_sortable: Optional[bool] = None
    default_value: Optional[str] = None
    enum_values: Optional[List[EnumValueItem]] = None
    validation_regex: Optional[str] = None
    min_value: Optional[str] = None
    max_value: Optional[str] = None
    is_reference: Optional[bool] = None
    reference_model_id: Optional[UUID] = None
    is_computed: Optional[bool] = None
    compute_expr: Optional[str] = None
    compute_script: Optional[str] = None
    choice_webhook: Optional[Dict[str, Any]] = None
    choice_script: Optional[str] = None


class GlobalAttributeResponse(GlobalAttributeBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class ModelAttributeBase(BaseModel):
    attribute_id: UUID = Field(..., description="属性ID")
    is_required: bool = Field(False, description="是否必填")
    is_readonly: bool = Field(False, description="是否只读")
    default_show: bool = Field(True, description="是否默认显示")
    sort_order: int = Field(0, description="排序序号")
    group_name: Optional[str] = Field(None, max_length=50, description="属性分组名称")
    override_label: Optional[str] = Field(None, max_length=100, description="覆盖显示名")
    override_default: Optional[str] = Field(None, description="覆盖默认值")


class ModelAttributeCreate(ModelAttributeBase):
    pass


class ModelAttributeUpdate(BaseModel):
    is_required: Optional[bool] = None
    is_readonly: Optional[bool] = None
    default_show: Optional[bool] = None
    sort_order: Optional[int] = None
    group_name: Optional[str] = Field(None, max_length=50)
    override_label: Optional[str] = Field(None, max_length=100)
    override_default: Optional[str] = None


class ModelAttributeResponse(ModelAttributeBase):
    id: UUID
    model_id: UUID
    attribute: Optional[GlobalAttributeResponse] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ModelBaseV2(BaseModel):
    name: str = Field(..., max_length=100, description="模型名称")
    code: str = Field(..., max_length=50, description="模型代码")
    description: Optional[str] = Field(None, max_length=500, description="模型描述")
    category: str = Field(..., max_length=50, description="模型分类")
    icon: Optional[str] = Field(None, max_length=100, description="图标标识")
    color: Optional[str] = Field(None, max_length=20, description="显示颜色")
    is_root_model: bool = Field(False, description="是否为根节点模型(顶级资源)")
    unique_key_id: Optional[UUID] = Field(None, description="唯一标识属性ID")
    show_key_id: Optional[UUID] = Field(None, description="显示名称属性ID")


class ModelCreateV2(ModelBaseV2):
    attributes: List[ModelAttributeCreate] = Field(default_factory=list, description="属性列表")


class ModelUpdateV2(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    is_root_model: Optional[bool] = Field(None, description="是否为根节点模型")
    unique_key_id: Optional[UUID] = None
    show_key_id: Optional[UUID] = None
    attributes: Optional[List[ModelAttributeCreate]] = Field(None, description="属性列表(更新时替换全部)")


class ModelResponseV2(ModelBaseV2):
    id: UUID
    is_active: bool
    is_root_model: bool
    unique_key: Optional[GlobalAttributeResponse] = None
    show_key: Optional[GlobalAttributeResponse] = None
    attributes: List[ModelAttributeResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class OperationRecordBase(BaseModel):
    operate_type: OperateType = Field(..., description="操作类型")
    model_id: Optional[UUID] = Field(None, description="关联模型ID")
    instance_id: Optional[UUID] = Field(None, description="关联实例ID")
    origin: Optional[str] = Field(None, max_length=50, description="操作来源")
    ticket_id: Optional[str] = Field(None, max_length=100, description="关联工单ID")
    reason: Optional[str] = Field(None, description="操作原因")


class OperationRecordResponse(OperationRecordBase):
    id: UUID
    created_at: datetime
    created_by: Optional[str] = None
    attribute_histories: List["AttributeHistoryResponse"] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class AttributeHistoryResponse(BaseModel):
    id: UUID
    instance_id: UUID
    attribute_id: Optional[UUID] = None
    attribute_name: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


OperationRecordResponse.model_rebuild()
