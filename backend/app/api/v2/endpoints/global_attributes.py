from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.db.database import get_async_db
from app.models.meta_model_v2 import GlobalAttribute, Model
from app.schemas.v2 import (
    GlobalAttributeCreate, GlobalAttributeUpdate, GlobalAttributeResponse
)

router = APIRouter()


@router.get("/", response_model=List[GlobalAttributeResponse])
async def list_global_attributes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = None,
    type: Optional[str] = None,
    is_reference: Optional[bool] = None,
    is_computed: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """获取全局属性列表"""
    query = select(GlobalAttribute)
    
    if name:
        query = query.where(GlobalAttribute.name.ilike(f"%{name}%"))
    if type:
        query = query.where(GlobalAttribute.type == type)
    if is_reference is not None:
        query = query.where(GlobalAttribute.is_reference == is_reference)
    if is_computed is not None:
        query = query.where(GlobalAttribute.is_computed == is_computed)
    
    query = query.offset(skip).limit(limit).order_by(GlobalAttribute.created_at.desc())
    result = await db.execute(query)
    attributes = result.scalars().all()
    
    return attributes


@router.get("/{attr_id}", response_model=GlobalAttributeResponse)
async def get_global_attribute(
    attr_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """获取全局属性详情"""
    result = await db.execute(
        select(GlobalAttribute).where(GlobalAttribute.id == attr_id)
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="属性不存在")
    return attr


@router.post("/", response_model=GlobalAttributeResponse)
async def create_global_attribute(
    attr_in: GlobalAttributeCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建全局属性"""
    existed = await db.execute(
        select(GlobalAttribute).where(GlobalAttribute.name == attr_in.name)
    )
    if existed.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"属性名称 '{attr_in.name}' 已存在")
    
    if attr_in.is_reference and attr_in.reference_model_id:
        model_result = await db.execute(
            select(Model).where(Model.id == attr_in.reference_model_id)
        )
        if not model_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="引用的模型不存在")
    
    attr_data = attr_in.model_dump()
    attr = GlobalAttribute(**attr_data)
    db.add(attr)
    await db.commit()
    await db.refresh(attr)
    
    return attr


@router.put("/{attr_id}", response_model=GlobalAttributeResponse)
async def update_global_attribute(
    attr_id: UUID,
    attr_in: GlobalAttributeUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新全局属性"""
    result = await db.execute(
        select(GlobalAttribute).where(GlobalAttribute.id == attr_id)
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="属性不存在")
    
    update_data = attr_in.model_dump(exclude_unset=True)
    
    if "name" in update_data and update_data["name"] != attr.name:
        existed = await db.execute(
            select(GlobalAttribute).where(GlobalAttribute.name == update_data["name"])
        )
        if existed.scalar_one_or_none():
            raise HTTPException(status_code=400, detail=f"属性名称 '{update_data['name']}' 已存在")
    
    if update_data.get("is_reference") and update_data.get("reference_model_id"):
        model_result = await db.execute(
            select(Model).where(Model.id == update_data["reference_model_id"])
        )
        if not model_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="引用的模型不存在")
    
    for field, value in update_data.items():
        setattr(attr, field, value)
    
    await db.commit()
    await db.refresh(attr)
    
    return attr


@router.delete("/{attr_id}")
async def delete_global_attribute(
    attr_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    """删除全局属性"""
    from app.models.meta_model_v2 import ModelAttribute
    
    result = await db.execute(
        select(GlobalAttribute).where(GlobalAttribute.id == attr_id)
    )
    attr = result.scalar_one_or_none()
    if not attr:
        raise HTTPException(status_code=404, detail="属性不存在")
    
    ref_result = await db.execute(
        select(func.count(ModelAttribute.id)).where(ModelAttribute.attribute_id == attr_id)
    )
    ref_count = ref_result.scalar()
    if ref_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"属性 '{attr.name}' 正被 {ref_count} 个模型使用，无法删除"
        )
    
    await db.delete(attr)
    await db.commit()
    
    return {"message": "删除成功"}


@router.get("/check-name/{name}")
async def check_attribute_name(
    name: str,
    exclude_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """检查属性名称是否可用"""
    query = select(GlobalAttribute).where(GlobalAttribute.name == name)
    if exclude_id:
        query = query.where(GlobalAttribute.id != exclude_id)
    
    result = await db.execute(query)
    existed = result.scalar_one_or_none()
    
    return {"available": existed is None}
