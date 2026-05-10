from typing import List, Dict, Any, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, union_all, func
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
        """Get topology data using optimized BFS with batch queries."""
        nodes: Dict[str, Dict] = {}
        edges: Dict[str, Dict] = {}
        visited_nodes: Set[UUID] = set()
        queue: List[tuple[UUID, int]] = [(root_id, 0)]
        loaded_edge_counts: Dict[str, int] = {}
        
        # Fetch root node
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
            
            if current_depth >= depth:
                continue
                
            # Query relations (bidirectional)
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
            
            # Update current node's edge count
            loaded_edge_counts[str(current_id)] = len(relations)
            
            for rel in relations:
                is_source = rel.source_instance_id == current_id
                neighbor = rel.target_instance if is_source else rel.source_instance
                
                if not neighbor:
                    continue
                    
                edge_id = str(rel.id)
                if edge_id not in edges:
                    edges[edge_id] = TopologyService._format_edge(rel)
                
                neighbor_id_str = str(neighbor.id)
                loaded_edge_counts[neighbor_id_str] = loaded_edge_counts.get(neighbor_id_str, 0) + 1
                
                if neighbor.id not in visited_nodes:
                    nodes[neighbor_id_str] = TopologyService._format_node(neighbor)
                    visited_nodes.add(neighbor.id)
                    queue.append((neighbor.id, current_depth + 1))
        
        # Batch query for degree counts (optimized: single query with UNION)
        all_node_ids = list(visited_nodes)
        
        stmt_source = select(
            InstanceRelation.source_instance_id.label("id"), 
            func.count().label("count")
        ).where(InstanceRelation.source_instance_id.in_(all_node_ids)).group_by(InstanceRelation.source_instance_id)
            
        stmt_target = select(
            InstanceRelation.target_instance_id.label("id"), 
            func.count().label("count")
        ).where(InstanceRelation.target_instance_id.in_(all_node_ids)).group_by(InstanceRelation.target_instance_id)
        
        # Combine both queries into one execution using UNION ALL
        combined_stmt = union_all(stmt_source, stmt_target).alias("combined")
        degree_stmt = select(
            combined_stmt.c.id, 
            func.sum(combined_stmt.c.count).label("total_count")
        ).group_by(combined_stmt.c.id)
        
        real_counts: Dict[str, int] = {}
        res = await db.execute(degree_stmt)
        for row in res:
            real_counts[str(row.id)] = row.total_count
            
        # Update node data
        for node_id, node in nodes.items():
            visible_degree = sum(
                1 for edge in edges.values() 
                if edge["source"] == node_id or edge["target"] == node_id
            )
            real = real_counts.get(node_id, 0)
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
