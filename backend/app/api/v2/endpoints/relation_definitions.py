from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.db.database import get_async_db
from app.models.relation_engine import (
    RelationDefinition, InstanceRelation, MappingType, RelationDefinitionStatus
)
from app.models.meta_model_v2 import Model
from app.models.instance import Instance
from app.schemas.relation_engine import (
    RelationDefinitionCreate, RelationDefinitionUpdate, RelationDefinitionResponse,
    InstanceRelationCreate, InstanceRelationBatchCreate, InstanceRelationUpdate, InstanceRelationResponse,
    ModelBrief, InstanceBrief, MappingType as MappingTypeSchema, RelationDefinitionStatus as StatusSchema
)

router = APIRouter()


async def get_relation_definition_with_models(db: AsyncSession, relation_id: UUID) -> Optional[RelationDefinition]:
    result = await db.execute(
        select(RelationDefinition)
        .options(
            selectinload(RelationDefinition.source_model),
            selectinload(RelationDefinition.target_model)
        )
        .where(RelationDefinition.id == relation_id)
    )
    return result.scalar_one_or_none()


def relation_to_response(relation: RelationDefinition) -> dict:
    response = {
        "id": relation.id,
        "name": relation.name,
        "code": relation.code,
        "description": relation.description,
        "source_model_id": relation.source_model_id,
        "target_model_id": relation.target_model_id,
        "mapping_type": relation.mapping_type.value if relation.mapping_type else MappingType.ONE_TO_MANY.value,
        "relation_label": relation.relation_label,
        "inverse_label": relation.inverse_label,
        "is_hierarchical": relation.is_hierarchical,
        "is_bidirectional": relation.is_bidirectional,
        "min_cardinality": relation.min_cardinality,
        "max_cardinality": relation.max_cardinality,
        "status": relation.status.value if relation.status else RelationDefinitionStatus.DRAFT.value,
        "sort_order": relation.sort_order,
        "created_at": relation.created_at,
        "updated_at": relation.updated_at,
        "created_by": relation.created_by,
    }
    
    if relation.source_model:
        response["source_model"] = {
            "id": relation.source_model.id,
            "name": relation.source_model.name,
            "code": relation.source_model.code,
            "category": relation.source_model.category,
        }
    
    if relation.target_model:
        response["target_model"] = {
            "id": relation.target_model.id,
            "name": relation.target_model.name,
            "code": relation.target_model.code,
            "category": relation.target_model.category,
        }
    
    return response


@router.get("/", response_model=List[dict])
async def list_relation_definitions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    source_model_id: Optional[UUID] = None,
    target_model_id: Optional[UUID] = None,
    status: Optional[str] = None,
    is_hierarchical: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(RelationDefinition).options(
        selectinload(RelationDefinition.source_model),
        selectinload(RelationDefinition.target_model)
    )
    
    if source_model_id:
        query = query.where(RelationDefinition.source_model_id == source_model_id)
    if target_model_id:
        query = query.where(RelationDefinition.target_model_id == target_model_id)
    if status:
        query = query.where(RelationDefinition.status == status)
    if is_hierarchical is not None:
        query = query.where(RelationDefinition.is_hierarchical == is_hierarchical)
    
    query = query.offset(skip).limit(limit).order_by(RelationDefinition.sort_order, RelationDefinition.created_at)
    result = await db.execute(query)
    relations = result.scalars().unique().all()
    
    return [relation_to_response(r) for r in relations]


@router.post("/", response_model=dict)
async def create_relation_definition(
    relation_in: RelationDefinitionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    existed = await db.execute(
        select(RelationDefinition).where(RelationDefinition.code == relation_in.code)
    )
    if existed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"关系编码 '{relation_in.code}' 已存在")
    
    source_model = await db.execute(
        select(Model).where(Model.id == relation_in.source_model_id)
    )
    if not source_model.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="源模型不存在")
    
    target_model = await db.execute(
        select(Model).where(Model.id == relation_in.target_model_id)
    )
    if not target_model.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="目标模型不存在")
    
    if relation_in.source_model_id == relation_in.target_model_id:
        raise HTTPException(status_code=400, detail="源模型和目标模型不能相同")
    
    relation = RelationDefinition(
        name=relation_in.name,
        code=relation_in.code,
        description=relation_in.description,
        source_model_id=relation_in.source_model_id,
        target_model_id=relation_in.target_model_id,
        mapping_type=relation_in.mapping_type,
        relation_label=relation_in.relation_label,
        inverse_label=relation_in.inverse_label,
        is_hierarchical=relation_in.is_hierarchical,
        is_bidirectional=relation_in.is_bidirectional,
        min_cardinality=relation_in.min_cardinality,
        max_cardinality=relation_in.max_cardinality,
        sort_order=relation_in.sort_order,
        status=RelationDefinitionStatus.ACTIVE,
    )
    db.add(relation)
    await db.commit()
    
    relation = await get_relation_definition_with_models(db, relation.id)
    return relation_to_response(relation)


@router.get("/{relation_id}", response_model=dict)
async def get_relation_definition(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    relation = await get_relation_definition_with_models(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系定义不存在")
    return relation_to_response(relation)


@router.put("/{relation_id}", response_model=dict)
async def update_relation_definition(
    relation_id: UUID,
    relation_in: RelationDefinitionUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    relation = await get_relation_definition_with_models(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系定义不存在")
    
    update_data = relation_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(relation, field, value)
    
    await db.commit()
    relation = await get_relation_definition_with_models(db, relation_id)
    return relation_to_response(relation)


@router.delete("/{relation_id}")
async def delete_relation_definition(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    relation = await get_relation_definition_with_models(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系定义不存在")
    
    await db.delete(relation)
    await db.commit()
    
    return {"message": "删除成功"}


@router.post("/{relation_id}/activate")
async def activate_relation_definition(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    relation = await get_relation_definition_with_models(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系定义不存在")
    
    relation.status = RelationDefinitionStatus.ACTIVE
    await db.commit()
    
    return {"message": "激活成功"}


@router.post("/{relation_id}/deactivate")
async def deactivate_relation_definition(
    relation_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    relation = await get_relation_definition_with_models(db, relation_id)
    if not relation:
        raise HTTPException(status_code=404, detail="关系定义不存在")
    
    relation.status = RelationDefinitionStatus.INACTIVE
    await db.commit()
    
    return {"message": "停用成功"}
