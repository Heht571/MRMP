from typing import List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models.relation_engine import InstanceRelation, RelationDefinition
from app.models.instance import Instance

class RelationService:
    """
    关系服务 - 处理关系创建的逻辑校验
    """

    @staticmethod
    async def validate_creation(
        db: AsyncSession, 
        relation_def: RelationDefinition, 
        source: Instance, 
        target: Instance
    ):
        """
        验证关系创建是否合法
        """
        # 1. 空间校验 (Space Validation)
        # 如果关系类型暗示“包含”或“安装在”，且源设备有 U位信息
        # 假设 relation definition code 为 "contained_in" 或 "installed_on"
        # 且源实例有 u_position 和 u_height 属性
        
        spatial_relations = ["contained_in", "installed_on", "located_in"]
        if relation_def.code in spatial_relations:
            await RelationService._validate_u_position(db, relation_def, source, target)

    @staticmethod
    async def _validate_u_position(
        db: AsyncSession, 
        relation_def: RelationDefinition, 
        source: Instance, 
        target: Instance
    ):
        """
        校验 U 位是否重叠
        """
        # 获取源设备的 U 位信息
        source_data = source.data or {}
        u_pos = source_data.get("u_position")
        u_height = source_data.get("u_height", 1) # 默认为 1U
        
        # 如果没有 U 位信息，跳过校验 (可能只是逻辑包含，不是物理安装)
        if u_pos is None:
            return

        try:
            u_start = int(u_pos)
            u_end = u_start + int(u_height)
        except (ValueError, TypeError):
            # U位格式错误，忽略或报错？这里选择忽略，假设非数字U位不参与计算
            return

        # 获取目标容器(机柜)内已存在的设备
        # 查询所有 target 为 target.id 且关系类型相同的关系
        existing_relations_result = await db.execute(
            select(InstanceRelation)
            .options(selectinload(InstanceRelation.source_instance))
            .where(
                InstanceRelation.target_instance_id == target.id,
                InstanceRelation.relation_definition_id == relation_def.id
            )
        )
        existing_relations = existing_relations_result.scalars().all()
        
        for rel in existing_relations:
            other_inst = rel.source_instance
            if not other_inst or other_inst.id == source.id:
                continue
                
            other_data = other_inst.data or {}
            other_u_pos = other_data.get("u_position")
            other_u_height = other_data.get("u_height", 1)
            
            if other_u_pos is None:
                continue
                
            try:
                other_start = int(other_u_pos)
                other_end = other_start + int(other_u_height)
                
                # 检查重叠: max(start1, start2) < min(end1, end2)
                if max(u_start, other_start) < min(u_end, other_end):
                    raise HTTPException(
                        status_code=400,
                        detail=f"U位冲突: 当前设备({u_start}-{u_end}U) 与现有设备 '{other_inst.name}' ({other_start}-{other_end}U) 重叠"
                    )
            except (ValueError, TypeError):
                continue
