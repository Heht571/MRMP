from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import io
import csv
from collections import defaultdict
from app.db.database import get_async_db
from app.models.relation_engine import RelationDefinition, InstanceRelation, RelationDefinitionStatus
from app.models.instance import Instance
from app.models.meta_model_v2 import Model
from app.schemas.relation_engine import HierarchyNode, HierarchyTreeResponse, RelationType

router = APIRouter()


# ============ 缓存关系定义 ============
_relation_defs_cache: Optional[List[RelationDefinition]] = None
_relation_defs_by_source: Dict[UUID, List[RelationDefinition]] = {}


async def load_relation_defs(db: AsyncSession) -> None:
    """批量加载所有层级关系定义并按source_model_id分组"""
    global _relation_defs_cache, _relation_defs_by_source

    if _relation_defs_cache is not None:
        return

    result = await db.execute(
        select(RelationDefinition)
        .where(
            RelationDefinition.relation_type == RelationType.CONTAIN,
            RelationDefinition.status == RelationDefinitionStatus.ACTIVE
        )
    )
    _relation_defs_cache = result.scalars().all()

    _relation_defs_by_source = defaultdict(list)
    for rd in _relation_defs_cache:
        _relation_defs_by_source[rd.source_model_id].append(rd)


def get_relation_defs_by_source(model_id: UUID) -> List[RelationDefinition]:
    """获取指定模型的子关系定义"""
    return _relation_defs_by_source.get(model_id, [])


def clear_relation_defs_cache() -> None:
    """清除缓存"""
    global _relation_defs_cache, _relation_defs_by_source
    _relation_defs_cache = None
    _relation_defs_by_source = {}


# ============ 优化后的树构建 ============
async def build_forest_optimized(
    db: AsyncSession,
    max_depth: int = 10
) -> Dict[str, Any]:
    """优化后的层级森林构建 - 批量预加载"""

    # 1. 加载所有根模型
    root_models_result = await db.execute(
        select(Model).where(
            Model.is_active == True,
            Model.is_root_model == True
        )
    )
    root_models = root_models_result.scalars().all()

    if not root_models:
        return {"forest": [], "orphan_nodes": [], "total_trees": 0, "total_orphans": 0}

    root_model_ids = [m.id for m in root_models]

    # 2. 加载根模型的实例
    instances_result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
        .where(Instance.model_id.in_(root_model_ids))
    )
    all_instances = instances_result.scalars().unique().all()

    # 按 model_id 分组实例
    instances_by_model = defaultdict(list)
    instance_map = {}  # id -> instance
    for inst in all_instances:
        instances_by_model[inst.model_id].append(inst)
        instance_map[inst.id] = inst

    # 3. 批量加载所有层级关系定义
    await load_relation_defs(db)
    all_rel_defs = _relation_defs_cache
    all_rel_def_ids = [rd.id for rd in all_rel_defs]

    # 4. 批量加载所有实例关系
    if all_rel_def_ids:
        relations_result = await db.execute(
            select(InstanceRelation)
            .options(
                selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
            )
            .where(InstanceRelation.relation_definition_id.in_(all_rel_def_ids))
        )
        all_relations = relations_result.scalars().all()
    else:
        all_relations = []

    # 5. 建立关系索引: source_instance_id -> [relations]
    relations_by_source = defaultdict(list)
    for rel in all_relations:
        relations_by_source[rel.source_instance_id].append(rel)

    # 6. 构建树结构 (内存中)
    forest = []
    total_instance_count = 0

    for root_model in root_models:
        model_instances = instances_by_model.get(root_model.id, [])
        if not model_instances:
            continue

        tree_nodes = []
        for instance in model_instances:
            children = build_tree_recursive(
                instance.id,
                instance.model_id,
                relations_by_source,
                instance_map,
                max_depth,
                0,
                {instance.id}
            )
            tree_nodes.append({
                "id": instance.id,
                "name": instance.name,
                "code": instance.code,
                "model_id": instance.model_id,
                "model_name": root_model.name,
                "model_code": root_model.code,
                "model_color": root_model.color,
                "model_icon": root_model.icon,
                "data": instance.data or {},
                "relation_name": None,
                "children": children
            })
            total_instance_count += 1

        if tree_nodes:
            forest.append({
                "model_id": root_model.id,
                "model_name": root_model.name,
                "model_code": root_model.code,
                "model_color": root_model.color,
                "model_icon": root_model.icon,
                "nodes": tree_nodes
            })

    # 7. 处理孤立实例
    orphan_nodes = await get_orphan_instances_optimized(db, instance_map, relations_by_source)

    return {
        "forest": forest,
        "orphan_nodes": orphan_nodes,
        "total_trees": len(forest),
        "total_orphans": len(orphan_nodes)
    }


def build_tree_recursive(
    instance_id: UUID,
    model_id: UUID,
    relations_by_source: Dict[UUID, List],
    instance_map: Dict[UUID, Instance],
    max_depth: int,
    current_depth: int,
    visited: set
) -> List[Dict[str, Any]]:
    """在内存中递归构建子树"""
    if current_depth >= max_depth:
        return []

    if instance_id in visited:
        return []

    visited.add(instance_id)

    # 获取该实例的所有子关系
    relations = relations_by_source.get(instance_id, [])

    nodes = []
    for rel in relations:
        target_inst = rel.target_instance
        if not target_inst:
            continue

        target_id = target_inst.id
        if target_id in visited:
            continue

        # 检查目标实例的模型是否有子关系
        child_rels = get_relation_defs_by_source(target_inst.model_id)

        # 递归构建子节点
        children = build_tree_recursive(
            target_id,
            target_inst.model_id,
            relations_by_source,
            instance_map,
            max_depth,
            current_depth + 1,
            visited.copy()
        )

        node = {
            "id": target_id,
            "name": target_inst.name,
            "code": target_inst.code,
            "model_id": target_inst.model_id,
            "model_name": target_inst.model.name if target_inst.model else "",
            "model_code": target_inst.model.code if target_inst.model else "",
            "model_color": target_inst.model.color if target_inst.model else None,
            "model_icon": target_inst.model.icon if target_inst.model else None,
            "data": target_inst.data or {},
            "relation_name": "包含",
            "children": children
        }
        nodes.append(node)

    return nodes


async def get_orphan_instances_optimized(
    db: AsyncSession,
    instance_map: Dict[UUID, Instance],
    relations_by_source: Dict[UUID, List]
) -> List[Dict[str, Any]]:
    """优化后的孤立实例查询"""

    # 获取所有有父关联的实例ID
    linked_instance_ids = set()
    for rels in relations_by_source.values():
        for rel in rels:
            if rel.target_instance_id:
                linked_instance_ids.add(rel.target_instance_id)

    # 获取所有非根模型实例
    all_instances_result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
    )
    all_instances = all_instances_result.scalars().unique().all()

    # 根模型ID
    root_model_ids_result = await db.execute(
        select(Model.id).where(Model.is_root_model == True)
    )
    root_model_ids = set(row[0] for row in root_model_ids_result.fetchall())

    # 找出孤立实例
    orphan_nodes = []
    for inst in all_instances:
        # 非根模型，且没有父关联
        if inst.model_id not in root_model_ids and inst.id not in linked_instance_ids:
            orphan_nodes.append({
                "id": inst.id,
                "name": inst.name,
                "code": inst.code,
                "model_id": inst.model_id,
                "model_name": inst.model.name if inst.model else "",
                "model_code": inst.model.code if inst.model else "",
                "model_color": inst.model.color if inst.model else None,
                "model_icon": inst.model.icon if inst.model else None,
                "data": inst.data or {},
                "relation_name": None,
                "is_orphan": True,
                "children": []
            })

    return orphan_nodes


# ============ 原有接口保持兼容 ============
async def build_child_tree(
    db: AsyncSession,
    parent_instance_id: UUID,
    parent_model_id: UUID,
    max_depth: int = 10,
    current_depth: int = 0,
    visited: Optional[set] = None
) -> List[Dict[str, Any]]:
    """兼容旧接口 - 递归构建子树 (N+1问题，但保留用于单个节点查询)"""
    if current_depth >= max_depth:
        return []

    if visited is None:
        visited = set()

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

    instance_relations = await db.execute(
        select(InstanceRelation)
        .options(
            selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
        )
        .where(
            InstanceRelation.source_instance_id == parent_instance_id,
            InstanceRelation.relation_definition_id.in_([r.id for r in child_relations])
        )
    )
    child_instance_relations = instance_relations.scalars().all()

    nodes = []
    for ir in child_instance_relations:
        instance = ir.target_instance
        if not instance:
            continue
        if instance.id in visited:
            continue

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
    """获取根模型列表 (带实例计数)"""
    # 使用单个查询获取计数
    result = await db.execute(
        select(Model, func.count(Instance.id).label('count'))
        .outerjoin(Instance, Instance.model_id == Model.id)
        .where(
            Model.is_active == True,
            Model.is_root_model == True
        )
        .group_by(Model.id)
    )
    rows = result.all()

    root_models = []
    for model, count in rows:
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
    """兼容旧接口"""
    instances_result = await db.execute(
        select(Instance).options(selectinload(Instance.model))
    )
    all_instances = instances_result.scalars().unique().all()

    # 获取所有关系
    all_relations_result = await db.execute(
        select(InstanceRelation.target_instance_id)
    )
    linked_ids = set(row[0] for row in all_relations_result.fetchall())

    root_model_ids_result = await db.execute(
        select(Model.id).where(Model.is_root_model == True)
    )
    root_model_ids = set(row[0] for row in root_model_ids_result.fetchall())

    orphan_nodes = []
    for inst in all_instances:
        if inst.model_id not in root_model_ids and inst.id not in linked_ids:
            orphan_nodes.append({
                "id": inst.id,
                "name": inst.name,
                "code": inst.code,
                "model_id": inst.model_id,
                "model_name": inst.model.name if inst.model else "",
                "model_code": inst.model.code if inst.model else "",
                "model_color": inst.model.color if inst.model else None,
                "model_icon": inst.model.icon if inst.model else None,
                "data": inst.data or {},
                "relation_name": None,
                "is_orphan": True,
                "children": []
            })

    return orphan_nodes


# ============ API 端点 ============
@router.get("/forest", response_model=Dict[str, Any])
async def get_hierarchy_forest(
    max_depth: int = Query(10, ge=1, le=20, description="最大层级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取层级森林 - 优化版本"""
    # 清除缓存确保数据最新
    clear_relation_defs_cache()
    return await build_forest_optimized(db, max_depth)


@router.get("/tree/{model_id}", response_model=HierarchyTreeResponse)
async def get_hierarchy_tree(
    model_id: UUID,
    max_depth: int = Query(10, ge=1, le=20, description="最大层级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取指定模型的层级树"""
    model = await db.execute(
        select(Model).where(Model.id == model_id)
    )
    root_model = model.scalar_one_or_none()
    if not root_model:
        raise HTTPException(status_code=404, detail="模型不存在")

    # 加载实例
    result = await db.execute(
        select(Instance)
        .options(selectinload(Instance.model))
        .where(Instance.model_id == model_id)
    )
    root_instances = result.scalars().unique().all()

    # 加载关系定义
    await load_relation_defs(db)
    child_rels = get_relation_defs_by_source(model_id)
    rel_def_ids = [rd.id for rd in child_rels]

    # 加载实例关系
    if rel_def_ids:
        relations_result = await db.execute(
            select(InstanceRelation)
            .options(
                selectinload(InstanceRelation.target_instance).selectinload(Instance.model)
            )
            .where(InstanceRelation.relation_definition_id.in_(rel_def_ids))
        )
        all_relations = relations_result.scalars().all()
    else:
        all_relations = []

    # 建立索引
    relations_by_source = defaultdict(list)
    for rel in all_relations:
        relations_by_source[rel.source_instance_id].append(rel)

    instance_map = {inst.id: inst for inst in root_instances}

    nodes = []
    for instance in root_instances:
        children = build_tree_recursive(
            instance.id,
            instance.model_id,
            relations_by_source,
            instance_map,
            max_depth,
            0,
            {instance.id}
        )

        node = {
            "id": instance.id,
            "name": instance.name,
            "code": instance.code,
            "model_id": instance.model_id,
            "model_name": root_model.name,
            "model_code": root_model.code,
            "model_color": root_model.color,
            "model_icon": root_model.icon,
            "data": instance.data or {},
            "relation_name": None,
            "children": children
        }
        nodes.append(node)

    total_count = len(root_instances)

    return HierarchyTreeResponse(
        root_model_id=model_id,
        root_model_name=root_model.name,
        nodes=nodes,
        total_count=total_count
    )


@router.get("/children/{instance_id}", response_model=List[HierarchyNode])
async def get_instance_children(
    instance_id: UUID,
    max_depth: int = Query(1, ge=1, le=10, description="子级深度"),
    db: AsyncSession = Depends(get_async_db)
):
    """获取实例的直接子节点"""
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
    """获取实例的父节点"""
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
    """获取可用的根模型列表"""
    result = await db.execute(
        select(Model, func.count(Instance.id).label('count'))
        .outerjoin(Instance, Instance.model_id == Model.id)
        .where(
            Model.is_active == True,
            Model.is_root_model == True
        )
        .group_by(Model.id)
    )
    rows = result.all()

    root_models = []
    for model, count in rows:
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