import asyncio
import uuid
from sqlalchemy import select
from app.db.database import async_session_maker
from app.models.meta_model_v2 import Model, GlobalAttribute, AttributeType, ModelAttribute
from app.models.instance import Instance
from app.services.cmdb_service import ComputedAttributeService

async def test_computed_attributes():
    async with async_session_maker() as db:
        print("🚀 Starting Computed Attribute Test...")
        
        # 1. Create a test model "ServerSpec"
        model_id = uuid.uuid4()
        model = Model(
            id=model_id,
            name="ServerSpec",
            code=f"server_spec_{uuid.uuid4().hex[:8]}",
            category="test"
        )
        db.add(model)
        
        # 2. Create Attributes
        # CPU Cores
        attr_cpu = GlobalAttribute(
            name=f"cpu_{uuid.uuid4().hex[:8]}", 
            label="CPU Cores", 
            type=AttributeType.NUMBER
        )
        # RAM GB
        attr_ram = GlobalAttribute(
            name=f"ram_{uuid.uuid4().hex[:8]}", 
            label="RAM (GB)", 
            type=AttributeType.NUMBER
        )
        # Computed: Score = CPU * 2 + RAM
        attr_score = GlobalAttribute(
            name=f"score_{uuid.uuid4().hex[:8]}", 
            label="Performance Score", 
            type=AttributeType.NUMBER,
            is_computed=True,
            compute_expr=f"data['{attr_cpu.name}'] * 2 + data['{attr_ram.name}']"
        )
        
        db.add_all([attr_cpu, attr_ram, attr_score])
        await db.flush()
        
        # 3. Bind Attributes to Model
        db.add_all([
            ModelAttribute(model_id=model.id, attribute_id=attr_cpu.id),
            ModelAttribute(model_id=model.id, attribute_id=attr_ram.id),
            ModelAttribute(model_id=model.id, attribute_id=attr_score.id)
        ])
        await db.commit()
        
        print(f"✅ Created Model & Attributes. CPU: {attr_cpu.name}, RAM: {attr_ram.name}, Score: {attr_score.name}")
        
        # 4. Test Calculation Logic directly
        data = {
            attr_cpu.name: 4,
            attr_ram.name: 16
        }
        
        attributes_def = [
            {"name": attr_cpu.name, "is_computed": False},
            {"name": attr_ram.name, "is_computed": False},
            {"name": attr_score.name, "is_computed": True, "compute_expr": attr_score.compute_expr}
        ]
        
        result = ComputedAttributeService.calculate_attributes(data, attributes_def)
        print(f"📊 Input: CPU=4, RAM=16")
        print(f"🧮 Calculated Score: {result.get(attr_score.name)}")
        
        expected_score = 4 * 2 + 16 # 24
        if result.get(attr_score.name) == expected_score:
            print("✅ Calculation Correct!")
        else:
            print(f"❌ Calculation Failed! Expected {expected_score}, got {result.get(attr_score.name)}")

if __name__ == "__main__":
    asyncio.run(test_computed_attributes())
