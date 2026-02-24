from typing import List, Optional, Any, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, desc, Integer
from app.models.dashboard import DashboardWidget
from app.models.instance import Instance
from app.schemas.dashboard import WidgetCreate, WidgetUpdate

class DashboardService:
    @staticmethod
    async def get_widget_data(db: AsyncSession, widget_id: UUID) -> Optional[Dict[str, Any]]:
        """获取组件数据"""
        # 1. 获取组件配置
        query = select(DashboardWidget).where(DashboardWidget.id == widget_id)
        result = await db.execute(query)
        widget = result.scalar_one_or_none()
        
        if not widget:
            return None
            
        config = widget.config
        if not config:
            return {}
            
        model_id_str = config.get("model_id")
        if not model_id_str:
            return {"error": "Model ID not configured"}
            
        try:
            model_id = UUID(model_id_str)
        except ValueError:
            return {"error": "Invalid Model ID"}

        # 2. 根据类型获取数据
        if widget.type == "stat":
            return await DashboardService._get_stat_data(db, model_id, config)
        elif widget.type == "chart":
            return await DashboardService._get_chart_data(db, model_id, config)
        elif widget.type == "list":
            return await DashboardService._get_list_data(db, model_id, config)
            
        return {}

    @staticmethod
    async def _get_stat_data(db: AsyncSession, model_id: UUID, config: Dict) -> Dict:
        """获取统计数据"""
        aggregation = config.get("aggregation", "count")
        field = config.get("field")
        
        query = select(func.count(Instance.id)).where(Instance.model_id == model_id)
        
        if aggregation == "sum" and field:
            # 尝试转换字段值为数字并求和
            # 注意: 这里假设字段存储的是数字字符串
            query = select(func.sum(Instance.data[field].astext.cast(Integer))).where(Instance.model_id == model_id)
            
        result = await db.execute(query)
        value = result.scalar() or 0
        
        return {
            "value": value,
            "unit": config.get("unit", ""),
            "trend": 0, # TODO: 实现趋势计算
            "status": "success"
        }

    @staticmethod
    async def _get_chart_data(db: AsyncSession, model_id: UUID, config: Dict) -> Dict:
        """获取图表数据"""
        dimension = config.get("dimension")
        if not dimension:
            return {"error": "Dimension not configured"}
            
        # 判断是否为核心字段
        if dimension in ["status", "name", "code"]:
            group_col = getattr(Instance, dimension)
            select_col = group_col
        else:
            group_col = Instance.data[dimension].astext
            select_col = group_col

        # 按维度分组统计
        query = select(
            select_col, 
            func.count(Instance.id)
        ).where(
            Instance.model_id == model_id
        ).group_by(
            group_col
        )
        
        result = await db.execute(query)
        rows = result.all()
        
        return {
            "labels": [row[0] or "Unknown" for row in rows],
            "datasets": [
                {
                    "data": [row[1] for row in rows],
                    "name": config.get("title", "Count")
                }
            ]
        }

    @staticmethod
    async def _get_list_data(db: AsyncSession, model_id: UUID, config: Dict) -> Dict:
        """获取列表数据"""
        limit = config.get("limit", 10)
        sort_by = config.get("sort_by", "updated_at")
        
        query = select(Instance).where(
            Instance.model_id == model_id
        ).order_by(
            desc(Instance.updated_at)
        ).limit(limit)
        
        result = await db.execute(query)
        instances = result.scalars().all()
        
        columns = config.get("columns", [{"prop": "name", "label": "名称"}])
        
        data = []
        for inst in instances:
            item = inst.to_dict()
            row = {}
            for col in columns:
                prop = col.get("prop")
                if prop:
                    row[prop] = item.get(prop, "-")
            data.append(row)
            
        return {
            "data": data,
            "columns": columns
        }

    @staticmethod
    async def get_widgets(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[DashboardWidget]:
        query = select(DashboardWidget).filter(DashboardWidget.is_active == True).order_by(DashboardWidget.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def create_widget(db: AsyncSession, widget_in: WidgetCreate) -> DashboardWidget:
        db_widget = DashboardWidget(
            name=widget_in.name,
            type=widget_in.type.value,
            config=widget_in.config,
            layout=widget_in.layout,
            is_active=widget_in.is_active
        )
        db.add(db_widget)
        await db.commit()
        await db.refresh(db_widget)
        return db_widget

    @staticmethod
    async def update_widget(db: AsyncSession, widget_id: UUID, widget_in: WidgetUpdate) -> Optional[DashboardWidget]:
        query = select(DashboardWidget).where(DashboardWidget.id == widget_id)
        result = await db.execute(query)
        db_widget = result.scalar_one_or_none()
        
        if not db_widget:
            return None
            
        update_data = widget_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'type' and value:
                setattr(db_widget, field, value.value)
            else:
                setattr(db_widget, field, value)
            
        await db.commit()
        await db.refresh(db_widget)
        return db_widget

    @staticmethod
    async def delete_widget(db: AsyncSession, widget_id: UUID) -> bool:
        query = select(DashboardWidget).where(DashboardWidget.id == widget_id)
        result = await db.execute(query)
        db_widget = result.scalar_one_or_none()
        
        if not db_widget:
            return False
            
        await db.delete(db_widget)
        await db.commit()
        return True

    @staticmethod
    async def update_layout(db: AsyncSession, layouts: List[dict]) -> bool:
        try:
            for item in layouts:
                widget_id = item.get('id')
                layout = item.get('layout')
                if widget_id and layout:
                    stmt = update(DashboardWidget).where(DashboardWidget.id == widget_id).values(layout=layout)
                    await db.execute(stmt)
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            return False
