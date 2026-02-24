
import sys
print("Starting test script...", file=sys.stderr)

import asyncio
import uuid
import sys
import traceback
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, delete
from app.core.config import settings
from app.models.instance import Instance
from app.models.relation_engine import InstanceRelation, RelationDefinition
from app.models.model import Model
from app.services.topology_service import TopologyService
from app.db.database import Base

# Setup async engine for testing
async_engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

async def test_topology_expansion():
    print("Entering test_topology_expansion...", file=sys.stderr)
    async with AsyncSessionLocal() as db:
        print("Session created.", file=sys.stderr)
        try:
            # 1. Setup Data
            print("Creating test data...", file=sys.stderr)
            
            suffix = str(uuid.uuid4())[:8]
            model_a_code = f"model_a_{suffix}"
            model_b_code = f"model_b_{suffix}"
            
            # Create models
            model_a = Model(name=f"ModelA_{suffix}", code=model_a_code, category="device", icon="box", color="#ccc")
            model_b = Model(name=f"ModelB_{suffix}", code=model_b_code, category="device", icon="box", color="#ccc")
            db.add(model_a)
            db.add(model_b)
            await db.flush()
            
            # Create root instance (Model A)
            root = Instance(name="Root", code=f"ROOT_{suffix}", model_id=model_a.id)
            db.add(root)
            await db.flush()
            
            # Create child instance (Model B)
            child = Instance(name="Child", code=f"CHILD_{suffix}", model_id=model_b.id)
            db.add(child)
            await db.flush()
            
            # Create grandchild instance (Model A)
            grandchild = Instance(name="Grandchild", code=f"GCHILD_{suffix}", model_id=model_a.id)
            db.add(grandchild)
            await db.flush()
            
            # Create relation definition A -> B
            rel_def_ab = RelationDefinition(
                code=f"contains_ab_{suffix}", 
                name=f"Contains AB {suffix}", 
                relation_label="contains",
                source_model_id=model_a.id,
                target_model_id=model_b.id,
                is_hierarchical=False # Disable hierarchical to avoid strict checks if any
            )
            db.add(rel_def_ab)
            
            # Create relation definition B -> A
            rel_def_ba = RelationDefinition(
                code=f"contains_ba_{suffix}", 
                name=f"Contains BA {suffix}", 
                relation_label="contains",
                source_model_id=model_b.id,
                target_model_id=model_a.id,
                is_hierarchical=False
            )
            db.add(rel_def_ba)
            
            await db.flush()
            
            # Link Root(A) -> Child(B)
            rel1 = InstanceRelation(
                source_instance_id=root.id,
                target_instance_id=child.id,
                relation_definition_id=rel_def_ab.id
            )
            db.add(rel1)
            
            # Link Child(B) -> Grandchild(A)
            rel2 = InstanceRelation(
                source_instance_id=child.id,
                target_instance_id=grandchild.id,
                relation_definition_id=rel_def_ba.id
            )
            db.add(rel2)
            
            await db.commit()
            
            # 2. Test get_topology(depth=1) -> Should include Root and Child
            print("\nTesting get_topology(depth=1)...", file=sys.stderr)
            topo = await TopologyService.get_topology(db, root.id, depth=1)
            
            nodes = {n["id"]: n for n in topo["nodes"]}
            edges = topo["edges"]
            
            print(f"Nodes count: {len(nodes)}", file=sys.stderr)
            print(f"Edges count: {len(edges)}", file=sys.stderr)
            
            # Verify Root
            root_node = nodes[str(root.id)]
            print(f"Root Node: {root_node['label']}, has_more: {root_node['data']['has_more']}", file=sys.stderr)
            # Root has 1 visible edge (to Child), and 1 total edge (to Child). has_more should be False.
            assert root_node['data']['has_more'] == False, "Root should NOT have more"
            
            # Verify Child
            child_node = nodes[str(child.id)]
            print(f"Child Node: {child_node['label']}, has_more: {child_node['data']['has_more']}", file=sys.stderr)
            # Child has 1 visible edge (to Root), but 2 total edges (Root + Grandchild). has_more should be True.
            # Wait, visible_degree for Child in depth=1 query:
            # Edges returned: Only Root->Child.
            # So visible degree = 1.
            # Total degree = 2.
            
            # Note: The backend logic for has_more compares real degree with visible degree.
            # real degree is calculated from DB.
            # visible degree is calculated from returned edges.
            
            if not child_node['data']['has_more']:
                 print(f"Child Data: {child_node['data']}", file=sys.stderr)
            
            assert child_node['data']['has_more'] == True, "Child SHOULD have more"
            
            print("\nSuccess! Logic verified.", file=sys.stderr)
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            await db.rollback()
            raise e
        finally:
            # Cleanup (optional in a real test DB, but good practice)
            pass

if __name__ == "__main__":
    try:
        asyncio.run(test_topology_expansion())
    except Exception as e:
        print(f"Error in main: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
