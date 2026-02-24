from typing import List, Dict, Any, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.models.instance import Instance
from app.models.relation_engine import InstanceRelation, RelationDefinition

class TopologyService:
    @staticmethod
    async def get_topology(
        db: AsyncSession, 
        root_id: UUID, 
        depth: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取拓扑结构数据 (BFS)
        """
        nodes: Dict[str, Dict] = {}
        edges: Dict[str, Dict] = {}
        visited_nodes: Set[UUID] = set()
        queue: List[tuple[UUID, int]] = [(root_id, 0)]
        
        # 记录每个节点已加载的边数量，用于计算 has_more
        loaded_edge_counts: Dict[str, int] = {}
        
        # 获取根节点
        root_instance = await db.execute(
            select(Instance)
            .options(selectinload(Instance.model))
            .where(Instance.id == root_id)
        )
        root = root_instance.scalar_one_or_none()
        if not root:
            return {"nodes": [], "edges": []}
            
        nodes[str(root.id)] = TopologyService._format_node(root)
        visited_nodes.add(root.id)
        
        while queue:
            current_id, current_depth = queue.pop(0)
            
            # 无论是否达到深度限制，我们都需要计算 degree (度) 来判断 has_more
            # 但为了性能，我们只对当前层级节点查询关系
            # 如果 current_depth == depth，我们就不继续 BFS，但节点本身已经加载了
            
            if current_depth >= depth:
                continue
                
            # 查询关联关系 (双向)
            relations_result = await db.execute(
                select(InstanceRelation)
                .options(
                    selectinload(InstanceRelation.source_instance).selectinload(Instance.model),
                    selectinload(InstanceRelation.target_instance).selectinload(Instance.model),
                    selectinload(InstanceRelation.relation_definition)
                )
                .where(
                    or_(
                        InstanceRelation.source_instance_id == current_id,
                        InstanceRelation.target_instance_id == current_id
                    )
                )
            )
            relations = relations_result.scalars().all()
            
            # 更新当前节点的已加载边数
            loaded_edge_counts[str(current_id)] = len(relations)
            
            for rel in relations:
                # 确定邻居节点
                is_source = rel.source_instance_id == current_id
                neighbor = rel.target_instance if is_source else rel.source_instance
                
                if not neighbor:
                    continue
                    
                # 添加边
                edge_id = str(rel.id)
                if edge_id not in edges:
                    edges[edge_id] = TopologyService._format_edge(rel)
                
                # 更新邻居节点的已加载边数 (因为这是双向关系)
                neighbor_id_str = str(neighbor.id)
                loaded_edge_counts[neighbor_id_str] = loaded_edge_counts.get(neighbor_id_str, 0) + 1
                
                # 添加节点并入队
                if neighbor.id not in visited_nodes:
                    nodes[neighbor_id_str] = TopologyService._format_node(neighbor)
                    visited_nodes.add(neighbor.id)
                    queue.append((neighbor.id, current_depth + 1))

        # 计算 has_more 状态
        # 获取所有已加载节点的ID
        all_node_ids = list(visited_nodes)
        
        # 批量查询真实边数量
        # SELECT source_id, count(*) FROM relations WHERE source_id IN (...) GROUP BY source_id
        # + SELECT target_id, count(*) ...
        # 这里为了简单，我们遍历查询或者构建一个复杂的 group by
        # 使用 UNION ALL 来统计所有连接
        
        # 性能优化：只查询边界节点？不，所有节点都需要 update has_more
        # 但考虑到节点可能很多，我们限制查询
        
        from sqlalchemy import func, union_all
        
        stmt_source = select(InstanceRelation.source_instance_id.label("id"), func.count().label("count"))\
            .where(InstanceRelation.source_instance_id.in_(all_node_ids))\
            .group_by(InstanceRelation.source_instance_id)
            
        stmt_target = select(InstanceRelation.target_instance_id.label("id"), func.count().label("count"))\
            .where(InstanceRelation.target_instance_id.in_(all_node_ids))\
            .group_by(InstanceRelation.target_instance_id)
            
        # 分别执行并合并
        real_counts = {}
        
        res_source = await db.execute(stmt_source)
        for row in res_source:
            real_counts[str(row.id)] = real_counts.get(str(row.id), 0) + row.count
            
        res_target = await db.execute(stmt_target)
        for row in res_target:
            real_counts[str(row.id)] = real_counts.get(str(row.id), 0) + row.count
            
        # 更新节点数据
        for node_id, node in nodes.items():
            loaded = loaded_edge_counts.get(node_id, 0)
            real = real_counts.get(node_id, 0)
            # 如果真实边数 > 已加载边数，说明有更多
            # 注意：loaded_edge_counts 计算的是在当前 BFS 遍历中遇到的边。
            # 由于是无向图逻辑，每条边会被计数两次（source一次，target一次），
            # 但我们在 loaded_edge_counts 中确实也是这么累加的吗？
            # 实际上，上面的 loaded_edge_counts[current_id] = len(relations) 是对的。
            # 而 loaded_edge_counts[neighbor_id_str] += 1 可能会导致重复计数吗？
            # 不会，因为 BFS 是树状扩展，但如果有环，边可能被访问多次？
            # 实际上，只要边被加入 edges 字典，就应该算作 visible edge。
            # 更准确的方法是：遍历 edges 字典，统计每个节点的 degree。
            
            visible_degree = 0
            for edge in edges.values():
                if edge["source"] == node_id or edge["target"] == node_id:
                    visible_degree += 1
            
            node["data"]["has_more"] = real > visible_degree
            node["data"]["degree"] = real
            node["data"]["visible_degree"] = visible_degree
                    
        return {
            "nodes": list(nodes.values()),
            "edges": list(edges.values())
        }

    @staticmethod
    def _format_node(instance: Instance) -> Dict[str, Any]:
        return {
            "id": str(instance.id),
            "label": instance.name,
            "type": "custom",  # Vue Flow custom node type
            "data": {
                "code": instance.code,
                "model_name": instance.model.name if instance.model else "Unknown",
                "icon": instance.model.icon if instance.model else "box",
                "color": instance.model.color if instance.model else "#ccc",
                "attributes": instance.data
            }
        }

    @staticmethod
    def _format_edge(rel: InstanceRelation) -> Dict[str, Any]:
        return {
            "id": str(rel.id),
            "source": str(rel.source_instance_id),
            "target": str(rel.target_instance_id),
            "label": rel.relation_definition.relation_label if rel.relation_definition else "related",
            "type": "smoothstep", # Vue Flow edge type
            "data": {
                "relation_type": rel.relation_definition.code if rel.relation_definition else "unknown"
            }
        }
