from typing import Dict, List, Optional
from fastapi import HTTPException
from app.schemas.base import InstanceStatus

class LifecycleService:
    """
    生命周期服务 - 管理资源实例的状态流转
    """
    
    # 定义允许的状态转换
    ALLOWED_TRANSITIONS: Dict[InstanceStatus, List[InstanceStatus]] = {
        InstanceStatus.PLANNING: [InstanceStatus.CONSTRUCTION, InstanceStatus.RETIRED], # 规划 -> 建设 或 直接归档(取消)
        InstanceStatus.CONSTRUCTION: [InstanceStatus.ACTIVE, InstanceStatus.RETIRED], # 建设 -> 现网 或 归档(取消)
        InstanceStatus.ACTIVE: [InstanceStatus.RETIRED], # 现网 -> 退网
        InstanceStatus.RETIRED: [InstanceStatus.PLANNING], # 退网 -> 重新规划
    }
    
    @classmethod
    def validate_transition(cls, current_status: str, new_status: str):
        """
        验证状态转换是否合法
        """
        if current_status == new_status:
            return
            
        # 兼容字符串和枚举
        try:
            curr_enum = InstanceStatus(current_status)
            new_enum = InstanceStatus(new_status)
        except ValueError:
             raise HTTPException(status_code=400, detail=f"无效的状态值: {current_status} 或 {new_status}")

        allowed_next = cls.ALLOWED_TRANSITIONS.get(curr_enum, [])
        if new_enum not in allowed_next:
            raise HTTPException(
                status_code=400, 
                detail=f"禁止的状态转换: 无法从 '{curr_enum.value}' 变更为 '{new_enum.value}'。允许的目标状态: {[s.value for s in allowed_next]}"
            )

    @classmethod
    def can_delete(cls, status: str) -> bool:
        """
        判断是否允许删除
        只有 PLANNING 和 RETIRED 状态允许物理删除
        """
        try:
            status_enum = InstanceStatus(status)
        except ValueError:
            return False # 无效状态不允许删除
            
        if status_enum in [InstanceStatus.PLANNING, InstanceStatus.RETIRED]:
            return True
            
        return False
