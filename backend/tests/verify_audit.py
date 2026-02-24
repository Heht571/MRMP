import asyncio
import uuid
import sys
import os

# Add backend to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.db.database import async_session_maker
from app.models.instance import Instance
from app.models.meta_model_v2 import Model, OperationRecord, AttributeHistory
from app.services.audit_service import AuditService

async def verify_audit():
    async with async_session_maker() as db:
        print("🚀 Starting Audit Verification...")
        
        # 1. Create a test model "AuditTestModel"
        model_id = uuid.uuid4()
        model = Model(
            id=model_id,
            name=f"AuditTestModel_{uuid.uuid4().hex[:6]}",
            code=f"audit_test_{uuid.uuid4().hex[:8]}",
            category="test"
        )
        db.add(model)
        await db.commit()
        
        # 2. Create Instance
        instance_id = uuid.uuid4()
        instance = Instance(
            id=instance_id,
            model_id=model_id,
            name="TestInstance",
            code=f"TEST_{uuid.uuid4().hex[:6]}",
            status="planning",
            data={"cpu": 4}
        )
        db.add(instance)
        # Log Create
        await AuditService.log_create(db, instance, "admin")
        await db.commit()
        print("✅ Instance Created and Logged.")
        
        # 3. Update Instance
        # Need to fetch fresh instance to simulate real flow
        result = await db.execute(select(Instance).where(Instance.id == instance_id))
        instance = result.scalar_one()
        
        # Simulate Update Data
        new_data = {"name": "TestInstance_Updated", "status": "active", "data": {"cpu": 8}}
        
        # Log Update
        await AuditService.log_update(db, instance, new_data, "admin")
        
        # Apply Update (Manual apply to match logic)
        instance.name = new_data["name"]
        instance.status = new_data["status"]
        instance.data = new_data["data"]
        instance.version += 1
        
        await db.commit()
        print("✅ Instance Updated and Logged.")
        
        # 4. Verify Logs
        # Check OperationRecord
        result = await db.execute(select(OperationRecord).where(OperationRecord.instance_id == instance_id))
        records = result.scalars().all()
        print(f"📊 Found {len(records)} Operation Records (Expected 2: Create + Update)")
        
        create_record = next((r for r in records if r.operate_type == "create"), None)
        update_record = next((r for r in records if r.operate_type == "update"), None)
        
        if create_record and update_record:
            print("✅ Both Create and Update records found.")
        else:
            print("❌ Missing records!")
            # Debug info
            for r in records:
                print(f"Record: {r.operate_type} at {r.created_at}")
            return

        # Check AttributeHistory for Update
        result = await db.execute(select(AttributeHistory).where(AttributeHistory.record_id == update_record.id))
        histories = result.scalars().all()
        print(f"📊 Found {len(histories)} Attribute Changes in Update")
        
        changes = {h.attribute_name: (h.old_value, h.new_value) for h in histories}
        print(f"Changes: {changes}")
        
        # Verify specific changes
        if changes.get("name") == ("TestInstance", "TestInstance_Updated"):
            print("✅ Name change logged correctly.")
        else:
            print(f"❌ Name change mismatch: {changes.get('name')}")
            
        if changes.get("status") == ("planning", "active"):
            print("✅ Status change logged correctly.")
        else:
            print(f"❌ Status change mismatch: {changes.get('status')}")
            
        # JSON numbers might be stored as strings in history, "4" vs "8"
        if changes.get("cpu") == ("4", "8"): 
             print("✅ CPU change logged correctly.")
        else:
             print(f"❌ CPU change mismatch: {changes.get('cpu')}")

if __name__ == "__main__":
    asyncio.run(verify_audit())