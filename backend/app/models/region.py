import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SQLEnum, func, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
import enum


class RegionLevel(str, enum.Enum):
    PROVINCE = "province"
    CITY = "city"
    DISTRICT = "district"
    PLANNING_AREA = "planning_area"


class AreaType(str, enum.Enum):
    IMPORTANT_AGG = "IMPORTANT_AGG"
    INTEGRATED_SERVICE = "INTEGRATED_SERVICE"
    RURAL_HOTSPOT = "RURAL_HOTSPOT"


class Region(Base):
    """
    区域层级模型 - 支持省/市/区县/规划区四级结构
    规划区层级可指定 area_type 用于分类管理:
    - IMPORTANT_AGG: 重要汇聚区 (每区2个重要汇聚机房)
    - INTEGRATED_SERVICE: 综合业务区 (每区1-2个普通汇聚机房)
    - RURAL_HOTSPOT: 城区热点区/乡镇区域 (每区1个业务汇聚机房)
    """
    __tablename__ = "regions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="区域名称")
    code = Column(String(50), unique=True, nullable=False, comment="区域编码")
    
    parent_id = Column(UUID(as_uuid=True), ForeignKey("regions.id"), nullable=True, comment="父级区域ID")
    level = Column(SQLEnum(RegionLevel), nullable=False, comment="区域层级")
    
    area_type = Column(
        SQLEnum(AreaType), 
        nullable=True, 
        comment="区域类型(仅规划区使用): IMPORTANT_AGG/INTEGRATED_SERVICE/RURAL_HOTSPOT"
    )
    
    description = Column(String(500), nullable=True, comment="区域描述")
    
    planned_room_count = Column(Integer, default=0, comment="规划机房数量")
    actual_room_count = Column(Integer, default=0, comment="实际机房数量")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    parent = relationship("Region", remote_side=[id], backref="children")
    
    def __repr__(self):
        return f"<Region {self.name} ({self.level.value})>"
    
    @property
    def full_path(self):
        """获取完整路径"""
        try:
            path = [self.name]
            parent = self.parent if 'parent' in self.__dict__ else None
            while parent:
                path.insert(0, parent.name)
                parent = parent.parent if 'parent' in parent.__dict__ else None
            return " / ".join(path)
        except Exception:
            return self.name
    
    @property
    def area_type_display(self):
        """区域类型显示名称"""
        type_map = {
            AreaType.IMPORTANT_AGG: "重要汇聚区",
            AreaType.INTEGRATED_SERVICE: "综合业务区",
            AreaType.RURAL_HOTSPOT: "城区热点区/乡镇区域"
        }
        return type_map.get(self.area_type, "-")
    
    @property
    def expected_room_count(self):
        """期望机房数量"""
        count_map = {
            AreaType.IMPORTANT_AGG: 2,
            AreaType.INTEGRATED_SERVICE: 2,
            AreaType.RURAL_HOTSPOT: 1
        }
        return count_map.get(self.area_type, 0)
