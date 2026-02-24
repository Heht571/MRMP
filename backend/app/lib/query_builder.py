from typing import List, Dict, Any, Optional
from sqlalchemy.sql import Select, and_, or_, cast, not_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import String, Integer, Float, Boolean, DateTime
from app.models.instance import Instance

class QueryBuilder:
    """
    JSONB 查询构建器
    
    支持的操作符:
    - eq: 等于
    - ne: 不等于
    - gt: 大于
    - lt: 小于
    - gte: 大于等于
    - lte: 小于等于
    - like: 包含 (字符串)
    - ilike: 包含 (忽略大小写)
    - in: 在列表中
    - not_in: 不在列表中
    - is_null: 为空
    - not_null: 不为空
    
    Filter 结构:
    [
        {
            "field": "cpu_cores",
            "operator": "gt",
            "value": 4
        },
        {
            "field": "status",
            "operator": "eq",
            "value": "active"
        }
    ]
    """
    
    OPERATORS = {
        "eq": lambda col, val: col == val,
        "ne": lambda col, val: col != val,
        "gt": lambda col, val: col > val,
        "lt": lambda col, val: col < val,
        "gte": lambda col, val: col >= val,
        "lte": lambda col, val: col <= val,
        "like": lambda col, val: col.like(f"%{val}%"),
        "ilike": lambda col, val: col.ilike(f"%{val}%"),
        "in": lambda col, val: col.in_(val),
        "not_in": lambda col, val: not_(col.in_(val)),
        "is_null": lambda col, val: col.is_(None),
        "not_null": lambda col, val: col.isnot(None),
    }

    @classmethod
    def apply_filters(cls, query: Select, filters: List[Dict[str, Any]]) -> Select:
        if not filters:
            return query
            
        conditions = []
        for f in filters:
            field = f.get("field")
            operator = f.get("operator", "eq")
            value = f.get("value")
            
            if not field or operator not in cls.OPERATORS:
                continue
                
            # 处理基本字段
            if field in ["name", "code", "model_id", "created_at", "updated_at"]:
                col = getattr(Instance, field)
                if operator in cls.OPERATORS:
                    conditions.append(cls.OPERATORS[operator](col, value))
            
            # 处理 JSONB 字段 (data)
            else:
                json_col = Instance.data[field]
                
                if operator in ["is_null", "not_null"]:
                    if operator == "is_null":
                        # JSONB checking for null is tricky, let's simplify
                        conditions.append(or_(Instance.data.has_key(field) == False, json_col.astext == 'null'))
                    else:
                        conditions.append(and_(Instance.data.has_key(field), json_col.astext != 'null'))
                    continue

                col = json_col.astext
                val_to_compare = value

                # Type casting for comparison
                if operator in ["gt", "lt", "gte", "lte"]:
                    if isinstance(value, (int, float)):
                        col = cast(json_col.astext, Float)
                        val_to_compare = value
                    else:
                         val_to_compare = str(value)

                elif isinstance(value, bool):
                    col = cast(json_col.astext, Boolean)
                    val_to_compare = value
                else:
                    if isinstance(value, (list, tuple)):
                        val_to_compare = [str(v) for v in value]
                    else:
                        val_to_compare = str(value)
                
                conditions.append(cls.OPERATORS[operator](col, val_to_compare))
                    
        if conditions:
            query = query.where(and_(*conditions))
            
        return query
