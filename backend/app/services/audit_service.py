from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.meta_model_v2 import OperationRecord, AttributeHistory, OperateType
from app.models.instance import Instance
import json

class AuditService:
    """
    审计服务 - 负责记录资源实例的所有变更历史
    """
    
    @staticmethod
    async def log_create(
        db: AsyncSession, 
        instance: Instance, 
        user_name: str, 
        origin: str = "API"
    ):
        """记录创建操作"""
        record = OperationRecord(
            operate_type=OperateType.CREATE,
            model_id=instance.model_id,
            instance_id=instance.id,
            origin=origin,
            created_by=user_name
        )
        db.add(record)
        await db.flush() # Ensure record gets an ID if needed, though SQLAlchemy usually handles relationships via object reference
        
        # 记录初始属性值
        if instance.data:
            for key, value in instance.data.items():
                history = AttributeHistory(
                    record_id=record.id,
                    instance_id=instance.id,
                    attribute_name=key,
                    old_value=None,
                    new_value=json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                )
                db.add(history)
                
        # 记录核心属性
        core_attrs = [("name", instance.name), ("code", instance.code), ("status", instance.status)]
        for key, value in core_attrs:
            if value:
                history = AttributeHistory(
                    record_id=record.id,
                    instance_id=instance.id,
                    attribute_name=key,
                    old_value=None,
                    new_value=str(value)
                )
                db.add(history)

    @staticmethod
    async def log_update(
        db: AsyncSession, 
        old_instance: Instance, 
        new_data: Dict[str, Any], 
        user_name: str, 
        origin: str = "API"
    ):
        """记录更新操作"""
        changes: List[Tuple[str, Any, Any]] = []
        
        # 1. 检查核心字段变更
        if "name" in new_data and new_data["name"] != old_instance.name:
            changes.append(("name", old_instance.name, new_data["name"]))
            
        if "code" in new_data and new_data["code"] != old_instance.code:
            changes.append(("code", old_instance.code, new_data["code"]))
            
        if "status" in new_data and new_data["status"] != old_instance.status:
            changes.append(("status", old_instance.status, new_data["status"]))
            
        # 2. 检查动态属性变更
        if "data" in new_data:
            old_dynamic = old_instance.data or {}
            new_dynamic = new_data["data"]
            
            # 检查修改和新增
            for key, new_val in new_dynamic.items():
                old_val = old_dynamic.get(key)
                
                # 简单比较，如果是复杂对象可能需要更精细的 Diff，这里暂用全等比较
                if old_val != new_val:
                    # 格式化值为字符串以便存储
                    old_str = json.dumps(old_val, ensure_ascii=False) if isinstance(old_val, (dict, list)) else str(old_val) if old_val is not None else None
                    new_str = json.dumps(new_val, ensure_ascii=False) if isinstance(new_val, (dict, list)) else str(new_val) if new_val is not None else None
                    
                    changes.append((key, old_str, new_str))
        
        if not changes:
            return

        # 创建操作记录
        record = OperationRecord(
            operate_type=OperateType.UPDATE,
            model_id=old_instance.model_id,
            instance_id=old_instance.id,
            origin=origin,
            created_by=user_name
        )
        db.add(record)
        await db.flush()
        
        # 创建属性变更历史
        for attr_name, old_val, new_val in changes:
            history = AttributeHistory(
                record_id=record.id,
                instance_id=old_instance.id,
                attribute_name=attr_name,
                old_value=str(old_val) if old_val is not None else None,
                new_value=str(new_val) if new_val is not None else None
            )
            db.add(history)

    @staticmethod
    async def log_delete(
        db: AsyncSession, 
        instance: Instance, 
        user_name: str, 
        origin: str = "API"
    ):
        """记录删除操作"""
        record = OperationRecord(
            operate_type=OperateType.DELETE,
            model_id=instance.model_id,
            instance_id=instance.id,
            origin=origin,
            created_by=user_name
        )
        db.add(record)
