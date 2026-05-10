from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import io
import csv
from app.db.database import get_async_db
from app.models.relation_engine import RelationDefinition, InstanceRelation, RelationDefinitionStatus
from app.models.instance import Instance
from app.models.meta_model_v2 import Model
from app.schemas.relation_engine import HierarchyNode, HierarchyTreeResponse, RelationType

router = APIRouter()


async def build_child_tree(
    db: AsyncSession,
    parent_instance_id: UUID,
    parent_model_id: UUID,
    max_depth: int = 10,
    current_depth: int = 0,
    visited: Optional[set] = None
) -> List[Dict[str, Any]]:
    if current_depth >= max_depth:
        return []

    if visited is None:
        visited = set()

    # 查找层级关系(contain)，只查询作为父模型的source方向
    child_relation_defs = await db.execute(
        select(RelationDefinition)
        .where(
            RelationDefinition.relation_type == RelationType.CONTAIN,
            RelationDefinition.status == RelationDefinitionStatus.ACTIVE,
            RelationDefinition.source_model_id == parent_model_id
        )
    )
    child_relations = child_relation_defs.scalars().all()

    if not child_relations:
        return []

    # Find instance relations where parent is source (contain: source=父, target=子)
    instance_relations = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.relation_definition)
        )
        .where(
            InstanceRelation.source_instance_id == parent_instance_id,
            InstanceRelation.relation_definition_id.in_([r.id for r in child_relations])
        )
    )
    child_instance_relations = instance_relations.scalars().all()

    nodes = []
    for ir in child_instance_relations:
        # 包含关系：source 是父，target 是子
        instance = ir.target_instance
        if not instance:
            continue
        if instance.id in visited:
            continue

        # 去重
        existing_ids = [n['id'] for n in nodes]
        if instance.id in existing_ids:
            continue

        visited_copy = visited.copy()
        visited_copy.add(instance.id)

        node = {
            "id": instance.id,
            "name": instance.name,
            "code": instance.code,
            "model_id": instance.model_id,
            "model_name": instance.model.name if instance.model else "",
            "model_code": instance.model.code if instance.model else "",
            "model_color": instance.model.color if instance.model else None,
            "model_icon": instance.model.icon if instance.model else None,
            "data": instance.data or {},
            "relation_name": "包含",
            "children": await build_child_tree(
                db,
                instance.id,
                instance.model_id,
                max_depth,
                current_depth + 1,
                visited_copy
            )
        }
        nodes.append(node)

    return nodes


async def get_root_models(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(Model).where(
            Model.is_active == True,
            Model.is_root_model == True  # Use explicit is_root_model flag
        )
    )
    models = result.scalars().all()

    root_models = []
    for model in models:
        instance_count = await db.execute(
            select(func.count()).select_from(Instance).where(Instance.model_id == model.id)
        )
        count = instance_count.scalar() or 0

        if count > 0:
            root_models.append({
                "id": model.id,
                "name": model.name,
                "code": model.code,
                "category": model.category,
                "icon": model.icon,
                "color": model.color,
                "instance_count": count,
                "is_root_model": True,
            })

    return root_models


async def get_orphan_instances(db: AsyncSession) -> List[Dict]:
    result = await db.execute(
        select(Model).where(
            Model.is_active == True,
            Model.is_root_model == False
        )
    )
    models = result.scalars().all()

    orphan_nodes = []
    for model in models:
        parent_relation = await db.execute(
            select(RelationDefinition).where(
                RelationDefinition.target_model_id == model.id,
                RelationDefinition.relation_type == RelationType.CONTAIN,
                RelationDefinition.status == RelationDefinitionStatus.ACTIVE
            ).limit(1)
        )
        has_parent_relation = parent_relation.scalar_one_or_none() is not None

        if has_parent_relation:
            linked_instance_ids = await db.execute(
                select(InstanceRelation.target_instance_id).where(
                    InstanceRelation.relation_definition_id.in_(
                        select(RelationDefinition.id).where(
                            RelationDefinition.target_model_id == model.id,
                            RelationDefinition.relation_type == RelationType.CONTAIN,
                            RelationDefinition.status == RelationDefinitionStatus.ACTIVE
                        )
                    )
                )
            )
            linked_ids = [row[0] for row in linked_instance_ids.fetchall()]

            orphan_query = select(Instance).options(
                selectinload(Instance.model)
            ).where(Instance.model_id == model.id)

            if linked_ids:
                orphan_query = orphan_query.where(Instance.id.not_in(linked_ids))

            orphans = await db.execute(orphan_query)
            orphan_instances = orphans.scalars().unique().all()

            for instance in orphan_instances:
                orphan_nodes.append({
                    "id": instance.id,
                    "name": instance.name,
                    "code": instance.code,
                    "model_id": instance.model_id,
                    "model_name": instance.model.name if instance.model else "",
                    "model_code": instance.model.code if instance.model else "",
                    "model_color": instance.model.color if instance.model else None,
                    "model_icon": instance.model.icon if instance.model else None,
                    "data": instance.data or {},
                    "relation_name": None,
                    "is_orphan": True,
                    "children": []
                })

    return orphan_nodes


@router.get("/forest", response_model=Dict[str, Any])
async def get_hierarchy_forest(
    max_depth: int = Query(10, ge=1, le=20, description="最大层级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    root_models = await get_root_models(db)

    forest = []

    for root_model in root_models:
        # Get ALL instances of this root model (not just those with relations)
        root_instances = await db.execute(
            select(Instance)
            .options(selectinload(Instance.model))
            .where(Instance.model_id == root_model["id"])
        )
        instances = root_instances.scalars().unique().all()

        tree_nodes = []
        for instance in instances:
            # Build children ONLY if there are actual instance relations
            children = await build_child_tree(
                db,
                instance.id,
                instance.model_id,
                max_depth,
                0,
                {instance.id}
            )

            node = {
                "id": instance.id,
                "name": instance.name,
                "code": instance.code,
                "model_id": instance.model_id,
                "model_name": instance.model.name if instance.model else "",
                "model_code": instance.model.code if instance.model else "",
                "model_color": instance.model.color if instance.model else None,
                "model_icon": instance.model.icon if instance.model else None,
                "data": instance.data or {},
                "relation_name": None,
                "children": children
            }
            tree_nodes.append(node)

        if tree_nodes:
            forest.append({
                "model_id": root_model["id"],
                "model_name": root_model["name"],
                "model_code": root_model["code"],
                "model_color": root_model["color"],
                "model_icon": root_model["icon"],
                "nodes": tree_nodes
            })

    orphan_nodes = await get_orphan_instances(db)

    return {
        "forest": forest,
        "orphan_nodes": orphan_nodes,
        "total_trees": len(forest),
        "total_orphans": len(orphan_nodes)
    }


@router.get("/tree/{model_id}", response_model=HierarchyTreeResponse)
async def get_hierarchy_tree(
    model_id: UUID,
    max_depth: int = Query(10, ge=1, le=20, description="最大层级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    model = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    root_model = model.scalar_one_or_none()
    if not root_model:
        raise HTTPException(status_code=404, detail="模型不存在")

    # Get ALL instances of this model (not just those with relations)
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
        .where(Instance.model_id == model_id)
    )
    root_instances = result.scalars().unique().all()

    nodes = []
    for instance in root_instances:
        # Build children ONLY if there are actual instance relations
        children = await build_child_tree(
            db,
            instance.id,
            instance.model_id,
            max_depth,
            0,
            {instance.id}
        )

        node = {
            "id": instance.id,
            "name": instance.name,
            "code": instance.code,
            "model_id": instance.model_id,
            "model_name": instance.model.name if instance.model else "",
            "model_code": instance.model.code if instance.model else "",
            "model_color": instance.model.color if instance.model else None,
            "model_icon": instance.model.icon if instance.model else None,
            "data": instance.data or {},
            "relation_name": None,
            "children": children
        }
        nodes.append(node)
    
    total_count = await db.execute(
        select(func.count()).select_from(Instance).where(Instance.model_id == model_id)
    )
    
    return HierarchyTreeResponse(
        root_model_id=model_id,
        root_model_name=root_model.name,
        nodes=nodes,
        total_count=total_count.scalar() or 0
    )


@router.get("/children/{instance_id}", response_model=List[HierarchyNode])
async def get_instance_children(
    instance_id: UUID,
    max_depth: int = Query(1, ge=1, le=10, description="子级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    instance = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
        .where(Instance.id == instance_id)
    )
    parent_instance = instance.scalar_one_or_none()
    if not parent_instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    
    child_nodes = await build_child_tree(
        db,
        parent_instance.id,
        parent_instance.model_id,
        max_depth,
        0,
        {instance_id}
    )
    
    return [HierarchyNode(**node) for node in child_nodes]


@router.get("/parents/{instance_id}", response_model=List[dict])
async def get_instance_parents(
    instance_id: UUID,
    db: AsyncSession = Depends(get_async_db)
):
    instance = await db.execute(
        select(Instance).where(Instance.id == instance_id)
    )
    if not instance.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="实例不存在")
    
    parent_relations = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model),
            selectinload(InstanceRelation.relation_definition)
        )
        .where(InstanceRelation.source_instance_id == instance_id)
    )
    relations = parent_relations.scalars().all()
    
    parents = []
    for rel in relations:
        if rel.target_instance:
            parents.append({
                "id": rel.target_instance.id,
                "name": rel.target_instance.name,
                "code": rel.target_instance.code,
                "model_id": rel.target_instance.model_id,
                "model_name": rel.target_instance.model.name if rel.target_instance.model else None,
                "relation_name": rel.relation_definition.inverse_label if rel.relation_definition else None,
            })
    
    return parents


@router.get("/available-root-models", response_model=List[dict])
async def get_available_root_models(
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(Model)
        .where(
            Model.is_active == True,
            Model.is_root_model == True  # Only models marked as root
        )
    )
    models = result.scalars().unique().all()

    root_models = []
    for model in models:
        instance_count = await db.execute(
            select(func.count()).select_from(Instance).where(Instance.model_id == model.id)
        )
        count = instance_count.scalar() or 0

        if count > 0:
            root_models.append({
                "id": model.id,
                "name": model.name,
                "code": model.code,
                "category": model.category,
                "icon": model.icon,
                "color": model.color,
                "instance_count": count,
                "is_root_model": True,
            })

    return root_models


def flatten_tree_to_rows(
    node: Dict[str, Any],
    rows: List[Dict[str, Any]],
    parent_path: str = "",
    level: int = 0
):
    current_path = f"{parent_path}/{node['name']}" if parent_path else node['name']
    
    row = {
        "层级": level + 1,
        "实例ID": str(node['id']),
        "实例名称": node['name'],
        "实例编码": node['code'] or "",
        "模型名称": node['model_name'],
        "模型编码": node['model_code'] or "",
        "路径": current_path,
        "父级关系": node.get('relation_name') or "",
    }
    
    if node.get('data'):
        for key, value in node['data'].items():
            if key not in row:
                row[f"属性_{key}"] = value
    
    rows.append(row)
    
    for child in node.get('children', []):
        flatten_tree_to_rows(child, rows, current_path, level + 1)


async def build_export_tree(
    db: AsyncSession,
    instance_id: UUID,
    max_depth: int = 20
) -> Dict[str, Any]:
    instance = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
        .where(Instance.id == instance_id)
    )
    inst = instance.scalar_one_or_none()
    if not inst:
        raise HTTPException(status_code=404, detail="实例不存在")
    
    node = {
        "id": inst.id,
        "name": inst.name,
        "code": inst.code,
        "model_id": inst.model_id,
        "model_name": inst.model.name if inst.model else "",
        "model_code": inst.model.code if inst.model else "",
        "data": inst.data or {},
        "relation_name": None,
        "children": await build_child_tree(
            db,
            inst.id,
            inst.model_id,
            max_depth,
            0,
            {inst.id}
        )
    }
    return node


@router.get("/export/{instance_id}")
async def export_instance_tree(
    instance_id: UUID,
    max_depth: int = Query(20, ge=1, le=50, description="最大导出层级深度"),
    format: str = Query("csv", regex="^(csv|json)$", description="导出格式"),
    db: AsyncSession = Depends(get_async_db)
):
    tree = await build_export_tree(db, instance_id, max_depth)
    
    if format == "json":
        import json
        json_content = json.dumps(tree, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=instance_{instance_id}_tree.json"
            }
        )
    
    rows = []
    flatten_tree_to_rows(tree, rows)
    
    if not rows:
        raise HTTPException(status_code=404, detail="没有可导出的数据")
    
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
    
    ordered_keys = ["层级", "实例ID", "实例名称", "实例编码", "模型名称", "模型编码", "路径", "父级关系"]
    attr_keys = sorted([k for k in all_keys if k.startswith("属性_")])
    ordered_keys.extend(attr_keys)
    
    final_keys = [k for k in ordered_keys if k in all_keys]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=final_keys, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename=instance_{instance_id}_tree.csv"
        }
    )


@router.get("/export-forest")
async def export_forest(
    max_depth: int = Query(20, ge=1, le=50, description="最大导出层级深度"),
    format: str = Query("csv", regex="^(csv|json)$", description="导出格式"),
    db: AsyncSession = Depends(get_async_db)
):
    forest_data = await get_hierarchy_forest(max_depth, db)
    
    if format == "json":
        import json
        json_content = json.dumps(forest_data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={
                "Content-Disposition": "attachment; filename=hierarchy_forest.json"
            }
        )
    
    rows = []
    for tree in forest_data.get("forest", []):
        for node in tree.get("nodes", []):
            flatten_tree_to_rows(node, rows)
    
    for node in forest_data.get("orphan_nodes", []):
        row = {
            "层级": 1,
            "实例ID": str(node['id']),
            "实例名称": node['name'],
            "实例编码": node['code'] or "",
            "模型名称": node['model_name'],
            "模型编码": node['model_code'] or "",
            "路径": f"[未关联] {node['name']}",
            "父级关系": "未关联",
        }
        if node.get('data'):
            for key, value in node['data'].items():
                if key not in row:
                    row[f"属性_{key}"] = value
        rows.append(row)
    
    if not rows:
        raise HTTPException(status_code=404, detail="没有可导出的数据")
    
    all_keys = set()
    for row in rows:
        all_keys.update(row.keys())
    
    ordered_keys = ["层级", "实例ID", "实例名称", "实例编码", "模型名称", "模型编码", "路径", "父级关系"]
    attr_keys = sorted([k for k in all_keys if k.startswith("属性_")])
    ordered_keys.extend(attr_keys)
    
    final_keys = [k for k in ordered_keys if k in all_keys]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=final_keys, extrasaction='ignore')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": "attachment; filename=hierarchy_forest.csv"
        }
    )
