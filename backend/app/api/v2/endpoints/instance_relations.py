from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.database import get_async_db
from app.models.relation_engine import InstanceRelation, RelationDefinition
from app.models.instance import Instance
from app.models.meta_model_v2 import Model
from app.services.relation_service import RelationService
from app.schemas.relation_engine import (
    InstanceRelationCreate, InstanceRelationBatchCreate, InstanceRelationUpdate, InstanceRelationResponse
)

router = APIRouter()


async def get_instance_relation_with_details(db: AsyncSession, relation_id: UUID) -> Optional[InstanceRelation]:
    result = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.relation_definition),
            selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
        )
        .where(InstanceRelation.id == relation_id)
    )
    return result.scalar_one_or_none()


def instance_relation_to_response(ir: InstanceRelation) -> dict:
    response = {
        "id": ir.id,
        "relation_definition_id": ir.relation_definition_id,
        "source_instance_id": ir.source_instance_id,
        "target_instance_id": ir.target_instance_id,
        "attributes": ir.attributes or {},
        "valid_from": ir.valid_from,
        "valid_to": ir.valid_to,
        "sort_order": ir.sort_order,
        "created_at": ir.created_at,
        "updated_at": ir.updated_at,
        "created_by": ir.created_by,
    }
    
    if ir.source_instance:
        response["source_instance"] = {
            "id": ir.source_instance.id,
            "name": ir.source_instance.name,
            "code": ir.source_instance.code,
            "model_id": ir.source_instance.model_id,
            "model_name": ir.source_instance.model.name if ir.source_instance.model else None,
        }
    
    if ir.target_instance:
        response["target_instance"] = {
            "id": ir.target_instance.id,
            "name": ir.target_instance.name,
            "code": ir.target_instance.code,
            "model_id": ir.target_instance.model_id,
            "model_name": ir.target_instance.model.name if ir.target_instance.model else None,
        }
    
    return response


@router.get("/", response_model=List[dict])
async def list_instance_relations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    relation_definition_id: Optional[UUID] = None,
    source_instance_id: Optional[UUID] = None,
    target_instance_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(InstanceRelation).options(
        selectinload(InstanceRelation.relation_definition),
        selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
        selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
    )
    
    if relation_definition_id:
        query = query.where(InstanceRelation.relation_definition_id == relation_definition_id)
    if source_instance_id:
        query = query.where(InstanceRelation.source_instance_id == source_instance_id)
    if target_instance_id:
        query = query.where(InstanceRelation.target_instance_id == target_instance_id)
    
    query = query.offset(skip).limit(limit).order_by(InstanceRelation.created_at.desc())
    result = await db.execute(query)
    relations = result.scalars().unique().all()
    
    return [instance_relation_to_response(r) for r in relations]


@router.post("/", response_model=dict)
async def create_instance_relation(
    relation_in: InstanceRelationCreate,
    db: AsyncSession = Depends(get_async_db)
):
    relation_def = await db.execute(
        select(RelationDefinition).where(RelationDefinition.id == relation_in.relation_definition_id)
    )
    if not relation_def.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="关系定义不存在")
    
    source_instance = await db.execute(
        select(Instance).where(Instance.id == relation_in.source_instance_id)
    )
    source = source_instance.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=400, detail="源实例不存在")
    
    target_instance = await db.execute(
        select(Instance).where(Instance.id == relation_in.target_instance_id)
    )
    target = target_instance.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=400, detail="目标实例不存在")
    
    if relation_in.source_instance_id == relation_in.target_instance_id:
        raise HTTPException(status_code=400, detail="源实例和目标实例不能相同")
    
    existed = await db.execute(
        select(InstanceRelation).where(
            InstanceRelation.relation_definition_id == relation_in.relation_definition_id,
            InstanceRelation.source_instance_id == relation_in.source_instance_id,
            InstanceRelation.target_instance_id == relation_in.target_instance_id
        )
    )
    if existed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该实例关系已存在")
    
    # 执行业务逻辑校验 (如 U位冲突)
    await RelationService.validate_creation(db, relation_def.scalar_one(), source, target)
    
    instance_relation = InstanceRelation(
        relation_definition_id=relation_in.relation_definition_id,
        source_instance_id=relation_in.source_instance_id,
        target_instance_id=relation_in.target_instance_id,
        attributes=relation_in.attributes,
        valid_from=relation_in.valid_from,
        valid_to=relation_in.valid_to,
        sort_order=relation_in.sort_order,
    )
    db.add(instance_relation)
    await db.commit()
    
    instance_relation = await get_instance_relation_with_details(db, instance_relation.id)
    return instance_relation_to_response(instance_relation)


@router.post("/batch", response_model=dict)
async def batch_create_instance_relations(
    batch_in: InstanceRelationBatchCreate,
    db: AsyncSession = Depends(get_async_db)
):
    relation_def = await db.execute(
        select(RelationDefinition).where(RelationDefinition.id == batch_in.relation_definition_id)
    )
    if not relation_def.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="关系定义不存在")
    
    created_count = 0
    skipped_count = 0
    errors = []
    
    for idx, relation_in in enumerate(batch_in.relations):
        try:
            if relation_in.source_instance_id == relation_in.target_instance_id:
                errors.append(f"第{idx + 1}条: 源实例和目标实例不能相同")
                continue
            
            existed = await db.execute(
                select(InstanceRelation).where(
                    InstanceRelation.relation_definition_id == batch_in.relation_definition_id,
                    InstanceRelation.source_instance_id == relation_in.source_instance_id,
                    InstanceRelation.target_instance_id == relation_in.target_instance_id
                )
            )
            if existed.scalar_one_or_none():
                skipped_count += 1
                continue
            
            instance_relation = InstanceRelation(
                relation_definition_id=batch_in.relation_definition_id,
                source_instance_id=relation_in.source_instance_id,
                target_instance_id=relation_in.target_instance_id,
                attributes=relation_in.attributes,
                valid_from=relation_in.valid_from,
                valid_to=relation_in.valid_to,
                sort_order=relation_in.sort_order,
            )
            db.add(instance_relation)
            created_count += 1
        except Exception as e:
            errors.append(f"第{idx + 1}条: {str(e)}")
    
    await db.commit()
    
    return {
        "message": "批量创建完成",
        "created_count": created_count,
        "skipped_count": skipped_count,
        "error_count": len(errors),
        "errors": errors[:10] if errors else []
    }


@router.get("/{relation_id}", response_model=dict)
async def get_instance_relation(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    instance_relation = await get_instance_relation_with_details(db, relation_id)
    if not instance_relation:
        raise HTTPException(status_code=404, detail="实例关系不存在")
    return instance_relation_to_response(instance_relation)


@router.put("/{relation_id}", response_model=dict)
async def update_instance_relation(
    relation_id: UUID,
    relation_in: InstanceRelationUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    instance_relation = await get_instance_relation_with_details(db, relation_id)
    if not instance_relation:
        raise HTTPException(status_code=404, detail="实例关系不存在")
    
    update_data = relation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(instance_relation, field, value)
    
    await db.commit()
    instance_relation = await get_instance_relation_with_details(db, relation_id)
    return instance_relation_to_response(instance_relation)


@router.delete("/{relation_id}")
async def delete_instance_relation(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    instance_relation = await get_instance_relation_with_details(db, relation_id)
    if not instance_relation:
        raise HTTPException(status_code=404, detail="实例关系不存在")
    
    await db.delete(instance_relation)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/batch-delete")
async def batch_delete_instance_relations(
    ids: List[UUID],
    db: AsyncSession = Depends(get_async_db)
):
    if not ids:
        raise HTTPException(status_code=400, detail="请提供要删除的关系ID")
    
    result = await db.execute(
        select(InstanceRelation).where(InstanceRelation.id.in_(ids))
    )
    relations = result.scalars().all()
    
    if not relations:
        raise HTTPException(status_code=404, detail="未找到要删除的关系")
    
    deleted_count = 0
    for relation in relations:
        await db.delete(relation)
        deleted_count += 1
    
    await db.commit()
    return {"message": "删除成功", "deleted_count": deleted_count}


@router.get("/by-source/{instance_id}", response_model=List[dict])
async def get_relations_by_source(
    instance_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.relation_definition),
            selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
        )
        .where(InstanceRelation.source_instance_id == instance_id)
    )
    relations = result.scalars().unique().all()
    return [instance_relation_to_response(r) for r in relations]


@router.get("/by-target/{instance_id}", response_model=List[dict])
async def get_relations_by_target(
    instance_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.relation_definition),
            selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
        )
        .where(InstanceRelation.target_instance_id == instance_id)
    )
    relations = result.scalars().unique().all()
    return [instance_relation_to_response(r) for r in relations]
