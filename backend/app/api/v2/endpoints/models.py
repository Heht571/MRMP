from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, delete
from sqlalchemy.orm import selectinload
from app.db.database import get_async_db
from app.models.meta_model_v2 import (
    Model, GlobalAttribute, ModelAttribute, ModelInheritance
)
from app.schemas.v2 import (
    ModelCreateV2, ModelUpdateV2, ModelAttributeResponse,
    GlobalAttributeResponse
)

router = APIRouter()


async def get_model_with_attributes(db: AsyncSession, model_id: UUID) -> Optional[Model]:
    result = await db.execute(
        select(Model)
        .options(
            selectinload(Model.model_attributes).selectinload(ModelAttribute.attribute),
            selectinload(Model.unique_key),
            selectinload(Model.show_key),
            selectinload(Model.parent_inheritances).selectinload(ModelInheritance.parent).selectinload(Model.model_attributes).selectinload(ModelAttribute.attribute)
        )
        .where(Model.id == model_id)
    )
    return result.scalar_one_or_none()


def model_to_response(model: Model) -> dict:
    attributes = []
    for ma in model.model_attributes:
        attr_dict = {
            "id": ma.id,
            "model_id": ma.model_id,
            "attribute_id": ma.attribute_id,
            "is_required": ma.is_required,
            "is_readonly": ma.is_readonly,
            "default_show": ma.default_show,
            "sort_order": ma.sort_order,
            "group_name": ma.group_name,
            "override_label": ma.override_label,
            "override_default": ma.override_default,
            "created_at": ma.created_at,
            "updated_at": ma.updated_at,
        }
        if ma.attribute:
            attr_dict["name"] = ma.attribute.name
            attr_dict["label"] = ma.override_label or ma.attribute.label
            attr_dict["type"] = ma.attribute.type.value
            attr_dict["description"] = ma.attribute.description
            attr_dict["is_unique"] = ma.attribute.is_unique
            attr_dict["is_indexed"] = ma.attribute.is_indexed
            attr_dict["default_value"] = ma.override_default or ma.attribute.default_value
            attr_dict["enum_values"] = ma.attribute.enum_values
        attributes.append(attr_dict)
    
    unique_key = None
    if model.unique_key:
        unique_key = {
            "id": model.unique_key.id,
            "name": model.unique_key.name,
            "label": model.unique_key.label,
            "type": model.unique_key.type.value,
        }
    
    show_key = None
    if model.show_key:
        show_key = {
            "id": model.show_key.id,
            "name": model.show_key.name,
            "label": model.show_key.label,
            "type": model.show_key.type.value,
        }
    
    return {
        "id": model.id,
        "name": model.name,
        "code": model.code,
        "description": model.description,
        "category": model.category,
        "icon": model.icon,
        "color": model.color,
        "is_active": model.is_active,
        "unique_key_id": model.unique_key_id,
        "show_key_id": model.show_key_id,
        "unique_key": unique_key,
        "show_key": show_key,
        "attributes": attributes,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "created_by": model.created_by,
    }


@router.get("/", response_model=List[dict])
async def list_models(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = None,
    code: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db)
):
    query = select(Model).options(
        selectinload(Model.model_attributes).selectinload(ModelAttribute.attribute),
        selectinload(Model.unique_key),
        selectinload(Model.show_key)
    )
    
    if category:
        query = query.where(Model.category == category)
    if code:
        query = query.where(Model.code == code)
    if is_active is not None:
        query = query.where(Model.is_active == is_active)
    
    query = query.offset(skip).limit(limit).order_by(Model.created_at)
    result = await db.execute(query)
    models = result.scalars().unique().all()
    
    return [model_to_response(m) for m in models]


@router.post("/", response_model=dict)
async def create_model(
    model_in: ModelCreateV2,
    db: AsyncSession = Depends(get_async_db)
):
    existed = await db.execute(
        select(Model).where(Model.code == model_in.code)
    )
    if existed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"模型编码 '{model_in.code}' 已存在")
    
    model = Model(
        name=model_in.name,
        code=model_in.code,
        description=model_in.description,
        category=model_in.category,
        icon=model_in.icon,
        color=model_in.color,
        unique_key_id=model_in.unique_key_id,
        show_key_id=model_in.show_key_id,
    )
    db.add(model)
    await db.flush()
    
    for attr_data in model_in.attributes:
        attr_result = await db.execute(
            select(GlobalAttribute).where(GlobalAttribute.id == attr_data.attribute_id)
        )
        if not attr_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"属性 {attr_data.attribute_id} 不存在")
        
        ma = ModelAttribute(
            model_id=model.id,
            attribute_id=attr_data.attribute_id,
            is_required=attr_data.is_required,
            is_readonly=attr_data.is_readonly,
            default_show=attr_data.default_show,
            sort_order=attr_data.sort_order,
            group_name=attr_data.group_name,
            override_label=attr_data.override_label,
            override_default=attr_data.override_default,
        )
        db.add(ma)
    
    await db.commit()
    
    model = await get_model_with_attributes(db, model.id)
    return model_to_response(model)


@router.get("/{model_id}", response_model=dict)
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    model = await get_model_with_attributes(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model_to_response(model)


@router.put("/{model_id}", response_model=dict)
async def update_model(
    model_id: UUID,
    model_in: ModelUpdateV2,
    db: AsyncSession = Depends(get_async_db)
):
    model = await get_model_with_attributes(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    update_data = model_in.model_dump(exclude_unset=True)
    attributes_data = update_data.pop("attributes", None)
    
    if "code" in update_data and update_data["code"] != model.code:
        existed = await db.execute(
            select(Model).where(Model.code == update_data["code"])
        )
        if existed.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"模型编码 '{update_data['code']}' 已存在")
    
    for field, value in update_data.items():
        setattr(model, field, value)
    
    if attributes_data is not None:
        for ma in model.model_attributes:
            await db.delete(ma)
        await db.flush()
        
        for attr_data in attributes_data:
            attr_id = attr_data.get("attribute_id") if isinstance(attr_data, dict) else attr_data.attribute_id
            attr_result = await db.execute(
                select(GlobalAttribute).where(GlobalAttribute.id == attr_id)
            )
            if not attr_result.scalar_one_or_none():
                raise HTTPException(status_code=400, detail=f"属性 {attr_id} 不存在")
            
            ma = ModelAttribute(
                model_id=model.id,
                attribute_id=attr_id,
                is_required=attr_data.get("is_required", False) if isinstance(attr_data, dict) else attr_data.is_required,
                is_readonly=attr_data.get("is_readonly", False) if isinstance(attr_data, dict) else attr_data.is_readonly,
                default_show=attr_data.get("default_show", True) if isinstance(attr_data, dict) else attr_data.default_show,
                sort_order=attr_data.get("sort_order", 0) if isinstance(attr_data, dict) else attr_data.sort_order,
                group_name=attr_data.get("group_name") if isinstance(attr_data, dict) else attr_data.group_name,
                override_label=attr_data.get("override_label") if isinstance(attr_data, dict) else attr_data.override_label,
                override_default=attr_data.get("override_default") if isinstance(attr_data, dict) else attr_data.override_default,
            )
            db.add(ma)
    
    await db.commit()
    
    model = await get_model_with_attributes(db, model_id)
    return model_to_response(model)


@router.delete("/{model_id}")
async def delete_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    from app.models.import_history import ImportHistory
    from app.models.relation_engine import RelationDefinition, InstanceRelation
    from app.models.instance import Instance
    
    model = await get_model_with_attributes(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    await db.execute(
        delete(InstanceRelation).where(
            InstanceRelation.relation_definition_id.in_(
                select(RelationDefinition.id).where(
                    or_(
                        RelationDefinition.source_model_id == model_id,
                        RelationDefinition.target_model_id == model_id
                    )
                )
            )
        )
    )
    
    await db.execute(
        delete(RelationDefinition).where(
            or_(
                RelationDefinition.source_model_id == model_id,
                RelationDefinition.target_model_id == model_id
            )
        )
    )
    
    await db.execute(
        delete(Instance).where(Instance.model_id == model_id)
    )
    
    await db.execute(
        delete(ImportHistory).where(ImportHistory.model_id == model_id)
    )
    
    for ma in model.model_attributes:
        await db.delete(ma)
    
    await db.delete(model)
    await db.commit()
    
    return {"message": "删除成功"}
