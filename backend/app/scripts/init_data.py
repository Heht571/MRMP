import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import async_session_maker
from app.models import (
    Region, RegionLevel, AreaType,
    Model, Attribute, AttributeType,
    Instance, InstanceStatus, EvolutionType,
    LifecycleMilestone, MilestoneStatus, MilestoneKey, MilestonePhase, MILESTONE_CONFIG,
    GlobalAttribute, ModelAttribute
)


async def init_meta_models(db: AsyncSession):
    """初始化元模型定义 - 机房模型"""
    
    result = await db.execute(select(Model).where(Model.code == "room"))
    existing_model = result.scalar_one_or_none()
    
    if existing_model:
        print("机房模型已存在，跳过初始化")
        return existing_model
    
    room_model = Model(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        name="汇聚机房",
        code="room",
        description="汇聚机房资源模型 - 支持重要汇聚、普通汇聚、业务汇聚三种类型",
        category="room",
        icon="room",
        color="#3498db",
        is_active=True
    )
    
    db.add(room_model)
    await db.flush()
    
    attributes = [
        Attribute(
            model_id=room_model.id,
            name="room_type",
            label="机房类型",
            description="机房类型分类",
            type=AttributeType.ENUM,
            is_required=True,
            is_indexed=True,
            enum_values=["IMPORTANT_AGG", "NORMAL_AGG", "SERVICE_AGG"],
            sort_order="1"
        ),
        Attribute(
            model_id=room_model.id,
            name="room_code",
            label="机房编码",
            description="机房唯一编码",
            type=AttributeType.STRING,
            is_required=True,
            is_unique=True,
            is_indexed=True,
            sort_order="2"
        ),
        Attribute(
            model_id=room_model.id,
            name="address",
            label="机房地址",
            description="机房详细地址",
            type=AttributeType.STRING,
            is_required=True,
            sort_order="3"
        ),
        Attribute(
            model_id=room_model.id,
            name="longitude",
            label="经度",
            description="GPS经度坐标",
            type=AttributeType.NUMBER,
            sort_order="4"
        ),
        Attribute(
            model_id=room_model.id,
            name="latitude",
            label="纬度",
            description="GPS纬度坐标",
            type=AttributeType.NUMBER,
            sort_order="5"
        ),
        Attribute(
            model_id=room_model.id,
            name="floor",
            label="楼层",
            description="机房所在楼层",
            type=AttributeType.STRING,
            sort_order="6"
        ),
        Attribute(
            model_id=room_model.id,
            name="area_size",
            label="机房面积",
            description="机房面积(平方米)",
            type=AttributeType.NUMBER,
            sort_order="7"
        ),
        Attribute(
            model_id=room_model.id,
            name="rack_count",
            label="机柜数量",
            description="机房内机柜数量",
            type=AttributeType.NUMBER,
            default_value="0",
            sort_order="8"
        ),
        Attribute(
            model_id=room_model.id,
            name="power_capacity",
            label="电力容量",
            description="机房电力容量(KVA)",
            type=AttributeType.NUMBER,
            sort_order="9"
        ),
        Attribute(
            model_id=room_model.id,
            name="has_generator",
            label="是否有油机",
            description="机房是否配备发电机组",
            type=AttributeType.BOOLEAN,
            default_value="false",
            sort_order="10"
        ),
        Attribute(
            model_id=room_model.id,
            name="has_ac",
            label="是否有空调",
            description="机房是否配备空调",
            type=AttributeType.BOOLEAN,
            default_value="false",
            sort_order="11"
        ),
        Attribute(
            model_id=room_model.id,
            name="ac_count",
            label="空调数量",
            description="机房空调数量",
            type=AttributeType.NUMBER,
            default_value="0",
            sort_order="12"
        ),
        Attribute(
            model_id=room_model.id,
            name="ownership",
            label="产权性质",
            description="机房产权性质",
            type=AttributeType.ENUM,
            enum_values=["SELF_OWNED", "RENTED", "SHARED"],
            sort_order="13"
        ),
        Attribute(
            model_id=room_model.id,
            name="rent_expire_date",
            label="租期到期日",
            description="如果是租赁机房，租期到期日期",
            type=AttributeType.DATE,
            sort_order="14"
        ),
        Attribute(
            model_id=room_model.id,
            name="contact_person",
            label="联系人",
            description="机房联系人姓名",
            type=AttributeType.STRING,
            sort_order="15"
        ),
        Attribute(
            model_id=room_model.id,
            name="contact_phone",
            label="联系电话",
            description="机房联系电话",
            type=AttributeType.STRING,
            sort_order="16"
        ),
        Attribute(
            model_id=room_model.id,
            name="responsible_unit",
            label="责任单位",
            description="机房管理责任单位",
            type=AttributeType.STRING,
            sort_order="17"
        ),
        Attribute(
            model_id=room_model.id,
            name="responsible_person",
            label="责任人",
            description="机房管理责任人",
            type=AttributeType.STRING,
            sort_order="18"
        ),
        Attribute(
            model_id=room_model.id,
            name="go_live_date",
            label="上线日期",
            description="机房正式上线日期",
            type=AttributeType.DATE,
            sort_order="19"
        ),
        Attribute(
            model_id=room_model.id,
            name="remarks",
            label="备注",
            description="机房备注信息",
            type=AttributeType.STRING,
            sort_order="20"
        ),
    ]
    
    db.add_all(attributes)
    await db.commit()
    
    print(f"✅ 已创建机房元模型，包含 {len(attributes)} 个属性")
    return room_model


async def init_sample_regions(db: AsyncSession):
    """初始化示例区域数据"""
    
    result = await db.execute(select(Region).limit(1))
    if result.scalar_one_or_none():
        print("区域数据已存在，跳过初始化")
        return
    
    province = Region(
        id=uuid.UUID("10000000-0000-0000-0000-000000000001"),
        name="XX省",
        code="XX",
        level=RegionLevel.PROVINCE,
        description="示例省份"
    )
    db.add(province)
    await db.flush()
    
    cities = [
        {
            "id": uuid.UUID("10000000-0000-0000-0000-000000000010"),
            "name": "XX市",
            "code": "XX-001",
            "parent_id": province.id,
            "level": RegionLevel.CITY
        },
        {
            "id": uuid.UUID("10000000-0000-0000-0000-000000000020"),
            "name": "YY市",
            "code": "YY-001",
            "parent_id": province.id,
            "level": RegionLevel.CITY
        }
    ]
    
    for city_data in cities:
        city = Region(**city_data)
        db.add(city)
    
    await db.flush()
    
    districts = [
        {
            "id": uuid.UUID("10000000-0000-0000-0000-000000000011"),
            "name": "A区",
            "code": "XX-001-A",
            "parent_id": cities[0]["id"],
            "level": RegionLevel.DISTRICT
        },
        {
            "id": uuid.UUID("10000000-0000-0000-0000-000000000012"),
            "name": "B区",
            "code": "XX-001-B",
            "parent_id": cities[0]["id"],
            "level": RegionLevel.DISTRICT
        },
        {
            "id": uuid.UUID("10000000-0000-0000-0000-000000000021"),
            "name": "C区",
            "code": "YY-001-C",
            "parent_id": cities[1]["id"],
            "level": RegionLevel.DISTRICT
        }
    ]
    
    for district_data in districts:
        district = Region(**district_data)
        db.add(district)
    
    await db.flush()
    
    planning_areas = [
        {
            "id": uuid.UUID("20000000-0000-0000-0000-000000000001"),
            "name": "A区重要汇聚区1",
            "code": "XX-001-A-IMP-01",
            "parent_id": districts[0]["id"],
            "level": RegionLevel.PLANNING_AREA,
            "area_type": AreaType.IMPORTANT_AGG,
            "planned_room_count": 2
        },
        {
            "id": uuid.UUID("20000000-0000-0000-0000-000000000002"),
            "name": "A区综合业务区1",
            "code": "XX-001-A-INT-01",
            "parent_id": districts[0]["id"],
            "level": RegionLevel.PLANNING_AREA,
            "area_type": AreaType.INTEGRATED_SERVICE,
            "planned_room_count": 2
        },
        {
            "id": uuid.UUID("20000000-0000-0000-0000-000000000003"),
            "name": "B区乡镇热点区1",
            "code": "XX-001-B-RUR-01",
            "parent_id": districts[1]["id"],
            "level": RegionLevel.PLANNING_AREA,
            "area_type": AreaType.RURAL_HOTSPOT,
            "planned_room_count": 1
        },
        {
            "id": uuid.UUID("20000000-0000-0000-0000-000000000004"),
            "name": "C区重要汇聚区1",
            "code": "YY-001-C-IMP-01",
            "parent_id": districts[2]["id"],
            "level": RegionLevel.PLANNING_AREA,
            "area_type": AreaType.IMPORTANT_AGG,
            "planned_room_count": 2
        }
    ]
    
    for area_data in planning_areas:
        area = Region(**area_data)
        db.add(area)
    
    await db.commit()
    print(f"✅ 已创建示例区域数据: 1省 2市 3区县 4规划区")


async def init_sample_rooms(db: AsyncSession):
    """初始化示例机房数据"""
    
    result = await db.execute(select(Instance).limit(1))
    if result.scalar_one_or_none():
        print("机房实例已存在，跳过初始化")
        return
    
    result = await db.execute(select(Model).where(Model.code == "room"))
    room_model = result.scalar_one_or_none()
    if not room_model:
        print("❌ 未找到机房模型，请先初始化元模型")
        return
    
    result = await db.execute(
        select(Region).where(Region.level == RegionLevel.PLANNING_AREA)
    )
    planning_areas = result.scalars().all()
    
    if not planning_areas:
        print("❌ 未找到规划区域，请先初始化区域数据")
        return
    
    sample_rooms = [
        {
            "name": "A区重要汇聚机房1",
            "code": "ROOM-IMP-001",
            "region_id": planning_areas[0].id,
            "status": InstanceStatus.ACTIVE,
            "evolution_type": EvolutionType.TARGET,
            "data": {
                "room_type": "IMPORTANT_AGG",
                "room_code": "ROOM-IMP-001",
                "address": "XX省XX市A区XX路XX号",
                "longitude": 116.404,
                "latitude": 39.915,
                "floor": "3F",
                "area_size": 120,
                "rack_count": 10,
                "power_capacity": 50,
                "has_generator": True,
                "has_ac": True,
                "ac_count": 2,
                "ownership": "SELF_OWNED",
                "contact_person": "张三",
                "contact_phone": "13800138000",
                "responsible_unit": "XX分公司",
                "responsible_person": "李四"
            }
        },
        {
            "name": "A区重要汇聚机房2",
            "code": "ROOM-IMP-002",
            "region_id": planning_areas[0].id,
            "status": InstanceStatus.CONSTRUCTION,
            "evolution_type": EvolutionType.TARGET,
            "data": {
                "room_type": "IMPORTANT_AGG",
                "room_code": "ROOM-IMP-002",
                "address": "XX省XX市A区YY路YY号",
                "floor": "2F",
                "area_size": 100,
                "ownership": "RENTED"
            }
        },
        {
            "name": "A区综合业务机房1",
            "code": "ROOM-INT-001",
            "region_id": planning_areas[1].id,
            "status": InstanceStatus.PLANNING,
            "evolution_type": EvolutionType.TARGET,
            "data": {
                "room_type": "NORMAL_AGG",
                "room_code": "ROOM-INT-001",
                "address": "XX省XX市A区ZZ路ZZ号"
            }
        },
        {
            "name": "B区乡镇机房1",
            "code": "ROOM-RUR-001",
            "region_id": planning_areas[2].id,
            "status": InstanceStatus.ACTIVE,
            "evolution_type": EvolutionType.ANCHOR,
            "data": {
                "room_type": "SERVICE_AGG",
                "room_code": "ROOM-RUR-001",
                "address": "XX省XX市B区乡镇XX村",
                "area_size": 50,
                "rack_count": 4,
                "has_ac": False
            }
        }
    ]
    
    for room_data in sample_rooms:
        instance = Instance(
            model_id=room_model.id,
            **room_data
        )
        db.add(instance)
        await db.flush()
        
        milestones = LifecycleMilestone.create_default_milestones(instance.id)
        db.add_all(milestones)
    
    await db.commit()
    print(f"✅ 已创建 {len(sample_rooms)} 个示例机房实例")


async def init_region_meta_model(db: AsyncSession):
    """初始化元模型定义 - 区域模型"""
    
    result = await db.execute(select(Model).where(Model.code == "region"))
    existing_model = result.scalar_one_or_none()
    
    if existing_model:
        print("区域模型已存在，跳过初始化")
        return existing_model
    
    region_model = Model(
        id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
        name="区域",
        code="region",
        description="行政区域及规划区域模型",
        category="resource",
        icon="place",
        color="#e67e22",
        is_active=True
    )
    
    db.add(region_model)
    await db.flush()
    
    # Global Attributes
    attr_level = GlobalAttribute(
        name="level",
        label="区域层级",
        description="区域行政层级",
        type=AttributeType.ENUM,
        enum_values=["PROVINCE", "CITY", "DISTRICT", "PLANNING_AREA"]
    )
    db.add(attr_level)
    
    attr_area_type = GlobalAttribute(
        name="area_type",
        label="区域类型",
        description="规划区域类型(仅规划区有效)",
        type=AttributeType.ENUM,
        enum_values=["IMPORTANT_AGG", "INTEGRATED_SERVICE", "RURAL_HOTSPOT"]
    )
    db.add(attr_area_type)
    
    attr_planned_room_count = GlobalAttribute(
        name="planned_room_count",
        label="规划机房数",
        description="该区域规划的汇聚机房数量",
        type=AttributeType.NUMBER,
        default_value="0"
    )
    db.add(attr_planned_room_count)
    
    await db.flush()
    
    # Model Attributes
    model_attrs = [
        ModelAttribute(
            model_id=region_model.id,
            attribute_id=attr_level.id,
            is_required=True,
            sort_order=1
        ),
        ModelAttribute(
            model_id=region_model.id,
            attribute_id=attr_area_type.id,
            is_required=False,
            sort_order=2
        ),
        ModelAttribute(
            model_id=region_model.id,
            attribute_id=attr_planned_room_count.id,
            is_required=False,
            sort_order=3
        )
    ]
    
    db.add_all(model_attrs)
    await db.commit()
    
    print(f"✅ 已创建区域元模型，包含 {len(model_attrs)} 个属性")
    return region_model


async def main():
    """主初始化函数"""
    print("=" * 60)
    print("🚀 开始初始化汇聚机房管理平台数据...")
    print("=" * 60)
    
    async with async_session_maker() as db:
        try:
            await init_meta_models(db)
            await init_region_meta_model(db)
            await init_sample_regions(db)
            await init_sample_rooms(db)
            
            print("\n" + "=" * 60)
            print("✅ 初始化完成！")
            print("=" * 60)
            print("\n📋 已创建内容:")
            print("  - 机房元模型 (含20个属性定义)")
            print("  - 区域元模型 (含3个属性定义)")
            print("  - 示例区域层级 (省/市/区县/规划区)")
            print("  - 示例机房实例 (含建设里程碑)")
            print("\n🔧 下一步操作:")
            print("  1. 启动后端服务: cd backend && uvicorn app.main:app --reload")
            print("  2. 访问API文档: http://localhost:8000/docs")
            print("  3. 启动前端服务: cd frontend && npm run dev")
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())
