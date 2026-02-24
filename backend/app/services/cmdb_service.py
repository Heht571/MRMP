import json
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.meta_model_v2 import (
    Model, ModelTrigger, ModelAttribute, OperationRecord, AttributeHistory,
    RelationHistory, TriggerHistory, TriggerEventType, TriggerActionType, OperateType
)
from app.models.instance import Instance
from app.models.relation import Relation


class HistoryService:
    """操作历史服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_record(
        self,
        operate_type: OperateType,
        model_id: Optional[UUID] = None,
        instance_id: Optional[UUID] = None,
        origin: Optional[str] = None,
        ticket_id: Optional[str] = None,
        reason: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> OperationRecord:
        """创建操作记录"""
        record = OperationRecord(
            operate_type=operate_type,
            model_id=model_id,
            instance_id=instance_id,
            origin=origin,
            ticket_id=ticket_id,
            reason=reason,
            created_by=created_by,
        )
        self.db.add(record)
        await self.db.flush()
        return record
    
    async def record_attribute_change(
        self,
        record_id: UUID,
        instance_id: UUID,
        attribute_name: str,
        attribute_id: Optional[UUID],
        old_value: Optional[str],
        new_value: Optional[str],
    ) -> AttributeHistory:
        """记录属性变更"""
        history = AttributeHistory(
            record_id=record_id,
            instance_id=instance_id,
            attribute_name=attribute_name,
            attribute_id=attribute_id,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(history)
        await self.db.flush()
        return history
    
    async def record_relation_change(
        self,
        record_id: UUID,
        source_id: UUID,
        target_id: UUID,
        relation_type: str,
        relation_id: Optional[UUID] = None,
        old_value: Optional[Dict] = None,
        new_value: Optional[Dict] = None,
    ) -> RelationHistory:
        """记录关系变更"""
        history = RelationHistory(
            record_id=record_id,
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            old_value=old_value,
            new_value=new_value,
        )
        self.db.add(history)
        await self.db.flush()
        return history
    
    async def record_instance_changes(
        self,
        instance: Instance,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        attribute_map: Dict[str, UUID],
        created_by: Optional[str] = None,
    ) -> OperationRecord:
        """记录实例的所有变更"""
        record = await self.create_record(
            operate_type=OperateType.UPDATE,
            model_id=instance.model_id,
            instance_id=instance.id,
            origin="api",
            created_by=created_by,
        )
        
        all_keys = set(old_data.keys()) | set(new_data.keys())
        for key in all_keys:
            old_val = old_data.get(key)
            new_val = new_data.get(key)
            if old_val != new_val:
                await self.record_attribute_change(
                    record_id=record.id,
                    instance_id=instance.id,
                    attribute_name=key,
                    attribute_id=attribute_map.get(key),
                    old_value=json.dumps(old_val, ensure_ascii=False) if old_val is not None else None,
                    new_value=json.dumps(new_val, ensure_ascii=False) if new_val is not None else None,
                )
        
        return record


class TriggerService:
    """触发器服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_active_triggers(
        self,
        model_id: UUID,
        event_type: TriggerEventType
    ) -> List[ModelTrigger]:
        """获取模型的活动触发器"""
        result = await self.db.execute(
            select(ModelTrigger).where(
                ModelTrigger.model_id == model_id,
                ModelTrigger.event_type == event_type,
                ModelTrigger.is_active == True
            )
        )
        return result.scalars().all()
    
    def evaluate_condition(
        self,
        condition: List[Dict],
        data: Dict[str, Any]
    ) -> bool:
        """评估触发条件"""
        if not condition:
            return True
        
        for cond in condition:
            attr = cond.get("attribute")
            operator = cond.get("operator")
            value = cond.get("value")
            
            actual = data.get(attr)
            
            if operator == "eq":
                if actual != value:
                    return False
            elif operator == "ne":
                if actual == value:
                    return False
            elif operator == "gt":
                if actual is None or actual <= value:
                    return False
            elif operator == "lt":
                if actual is None or actual >= value:
                    return False
            elif operator == "gte":
                if actual is None or actual < value:
                    return False
            elif operator == "lte":
                if actual is None or actual > value:
                    return False
            elif operator == "in":
                if actual not in value:
                    return False
            elif operator == "contains":
                if value not in str(actual):
                    return False
        
        return True
    
    async def execute_webhook(
        self,
        trigger: ModelTrigger,
        instance: Instance,
        old_data: Optional[Dict] = None,
    ) -> tuple[bool, Optional[str], Optional[Dict]]:
        """执行Webhook触发器"""
        config = trigger.action_config
        url = config.get("url")
        method = config.get("method", "POST").upper()
        headers = config.get("headers", {})
        body_template = config.get("body_template")
        timeout = config.get("timeout", 30)
        
        payload = {
            "trigger_name": trigger.name,
            "event_type": trigger.event_type.value,
            "instance_id": str(instance.id),
            "instance_name": instance.name,
            "model_id": str(instance.model_id),
            "data": instance.data,
            "old_data": old_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if body_template:
            try:
                body = body_template.format(**payload)
            except Exception as e:
                body = json.dumps(payload, ensure_ascii=False)
        else:
            body = json.dumps(payload, ensure_ascii=False)
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, headers=headers, content=body)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, content=body)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    response = await client.post(url, headers=headers, content=body)
                
                return response.status_code < 400, None, {"status_code": response.status_code, "body": response.text[:500]}
        
        except httpx.TimeoutException:
            return False, "请求超时", None
        except Exception as e:
            return False, str(e), None
    
    async def execute_script(
        self,
        trigger: ModelTrigger,
        instance: Instance,
        old_data: Optional[Dict] = None,
    ) -> tuple[bool, Optional[str], Optional[Dict]]:
        """执行脚本触发器"""
        config = trigger.action_config
        script = config.get("code", "")
        
        context = {
            "instance_id": str(instance.id),
            "instance_name": instance.name,
            "data": instance.data,
            "old_data": old_data or {},
            "result": None,
        }
        
        try:
            exec(script, {"__builtins__": __builtins__}, context)
            return True, None, {"result": context.get("result")}
        except Exception as e:
            return False, str(e), None
    
    async def execute_trigger(
        self,
        trigger: ModelTrigger,
        instance: Instance,
        old_data: Optional[Dict] = None,
    ) -> TriggerHistory:
        """执行触发器"""
        is_success = False
        error_message = None
        response_data = None
        
        if trigger.action_type == TriggerActionType.WEBHOOK:
            is_success, error_message, response_data = await self.execute_webhook(trigger, instance, old_data)
        elif trigger.action_type == TriggerActionType.SCRIPT:
            is_success, error_message, response_data = await self.execute_script(trigger, instance, old_data)
        elif trigger.action_type == TriggerActionType.EMAIL:
            pass
        
        history = TriggerHistory(
            trigger_id=trigger.id,
            instance_id=instance.id,
            is_success=is_success,
            error_message=error_message,
            response_data=response_data,
        )
        self.db.add(history)
        await self.db.flush()
        
        return history
    
    async def fire_triggers(
        self,
        model_id: UUID,
        event_type: TriggerEventType,
        instance: Instance,
        old_data: Optional[Dict] = None,
    ) -> List[TriggerHistory]:
        """触发所有符合条件的触发器"""
        triggers = await self.get_active_triggers(model_id, event_type)
        histories = []
        
        for trigger in triggers:
            if self.evaluate_condition(trigger.condition, instance.data or {}):
                history = await self.execute_trigger(trigger, instance, old_data)
                histories.append(history)
        
        return histories


class UniqueConstraintService:
    """唯一约束服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_unique_constraints(
        self,
        model_id: UUID,
        data: Dict[str, Any],
        exclude_instance_id: Optional[UUID] = None,
    ) -> Optional[str]:
        """验证唯一约束"""
        from app.models.meta_model_v2 import ModelUniqueConstraint
        
        result = await self.db.execute(
            select(ModelUniqueConstraint).where(ModelUniqueConstraint.model_id == model_id)
        )
        constraints = result.scalars().all()
        
        for constraint in constraints:
            attr_ids = constraint.attribute_ids
            if isinstance(attr_ids, str):
                attr_ids = json.loads(attr_ids)
            
            values = []
            attr_names = []
            for attr_id_str in attr_ids:
                from app.models.meta_model_v2 import GlobalAttribute, ModelAttribute
                
                attr_id = UUID(attr_id_str) if isinstance(attr_id_str, str) else attr_id_str
                
                attr_result = await self.db.execute(
                    select(GlobalAttribute).where(GlobalAttribute.id == attr_id)
                )
                attr = attr_result.scalar_one_or_none()
                if attr:
                    attr_names.append(attr.name)
                    values.append(data.get(attr.name))
            
            if all(v is not None for v in values):
                query = select(Instance).where(Instance.model_id == model_id)
                
                for name, value in zip(attr_names, values):
                    query = query.where(Instance.data[name].astext == str(value))
                
                if exclude_instance_id:
                    query = query.where(Instance.id != exclude_instance_id)
                
                result = await self.db.execute(query)
                if result.scalar_one_or_none():
                    return f"唯一约束 '{constraint.name}' 冲突: {' + '.join(attr_names)}"
        
        return None


class ComputedAttributeService:
    """计算属性服务"""
    
    @staticmethod
    def calculate_attributes(
        data: Dict[str, Any],
        attributes: List[Dict],
    ) -> Dict[str, Any]:
        """
        计算所有计算属性的值
        - data: 当前实例的所有数据
        - attributes: 包含属性定义的列表 (需包含 is_computed, compute_expr, name)
        """
        computed_data = data.copy()
        
        # 筛选出所有计算属性
        computed_attrs = [
            attr for attr in attributes 
            if attr.get("is_computed") and attr.get("compute_expr")
        ]
        
        if not computed_attrs:
            return computed_data
            
        # 简单的依赖解析：多轮计算以解决依赖问题 (最大3轮)
        # 比如: A = B + 1, B = C * 2. 如果先算A可能会出错，所以多跑几轮
        for _ in range(3):
            changed = False
            for attr in computed_attrs:
                attr_name = attr["name"]
                expr = attr["compute_expr"]
                
                try:
                    # 安全上下文: 仅允许访问数据和基本数学函数
                    # 注意: 这里的 data 包含了之前计算的结果
                    context = {
                        "data": computed_data,
                        "math": __import__("math"),
                        "datetime": __import__("datetime"),
                        # 允许直接访问属性名 (如果属性名是合法的变量名)
                        **computed_data
                    }
                    
                    # 尝试计算
                    # 替换表达式中的变量引用: ${field} -> data['field']
                    # 这里假设表达式是 Python 语法
                    
                    result = eval(expr, {"__builtins__": {}}, context)
                    
                    # 如果结果变化了，更新数据并标记
                    if computed_data.get(attr_name) != result:
                        computed_data[attr_name] = result
                        changed = True
                        
                except Exception as e:
                    # 计算失败时保留原值或设为 None，记录错误日志 (这里简单略过)
                    print(f"Error computing attribute {attr_name}: {e}")
                    pass
            
            if not changed:
                break
                
        return computed_data


class ReferenceService:
    """引用属性服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def validate_reference(
        self,
        reference_model_id: UUID,
        reference_value: Any,
    ) -> Optional[UUID]:
        """验证引用值是否有效"""
        if not reference_value:
            return None
        
        if isinstance(reference_value, dict):
            unique_value = reference_value.get("unique")
            if unique_value:
                result = await self.db.execute(
                    select(Instance).where(
                        Instance.model_id == reference_model_id,
                        Instance.data["unique"].astext == str(unique_value)
                    )
                )
                instance = result.scalar_one_or_none()
                if instance:
                    return instance.id
                return None
            return None
        
        try:
            instance_id = UUID(str(reference_value))
            result = await self.db.execute(
                select(Instance).where(
                    Instance.id == instance_id,
                    Instance.model_id == reference_model_id
                )
            )
            instance = result.scalar_one_or_none()
            return instance.id if instance else None
        except:
            return None
    
    async def resolve_reference(
        self,
        instance_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """解析引用实例"""
        result = await self.db.execute(
            select(Instance).where(Instance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        if instance:
            return {
                "id": str(instance.id),
                "name": instance.name,
                "model_id": str(instance.model_id),
                "data": instance.data,
            }
        return None
