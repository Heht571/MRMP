import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum as SQLEnum, func, Index, Integer, Date, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base


class MilestoneStatus(str, enum.Enum):
    PENDING = "PENDING"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class MilestonePhase(str, enum.Enum):
    INITIATION = "initiation"
    PROCUREMENT = "procurement"
    DESIGN = "design"
    CONSTRUCTION = "construction"
    FACILITY = "facility"
    COMPLETION = "completion"


class MilestoneKey(str, enum.Enum):
    PROJECT_APPROVAL = "project_approval"
    PROCUREMENT_DECISION = "procurement_decision"
    RECEIPT = "receipt"
    CERTIFICATE = "certificate"
    DESIGN_SURVEY = "design_survey"
    DESIGN_APPROVAL = "design_approval"
    MATERIALS_ARRIVAL = "materials_arrival"
    CONSTRUCTION = "construction"
    EXTERNAL_POWER = "external_power"
    DECORATION = "decoration"
    EQUIPMENT_INSTALL = "equipment_install"
    PIPELINE = "pipeline"
    CIRCUIT = "circuit"
    COMPLETION = "completion"
    GO_LIVE = "go_live"


MILESTONE_CONFIG = {
    MilestoneKey.PROJECT_APPROVAL: {
        "name": "购置立项批复/采购需求决策/建设专业立项批复",
        "phase": MilestonePhase.INITIATION,
        "duration_days": 0,
        "sort_order": 1
    },
    MilestoneKey.PROCUREMENT_DECISION: {
        "name": "采购方案决策/中标通知",
        "phase": MilestonePhase.PROCUREMENT,
        "duration_days": 75,
        "sort_order": 2
    },
    MilestoneKey.RECEIPT: {
        "name": "收货",
        "phase": MilestonePhase.PROCUREMENT,
        "duration_days": 45,
        "sort_order": 3
    },
    MilestoneKey.CERTIFICATE: {
        "name": "办理权证",
        "phase": MilestonePhase.PROCUREMENT,
        "duration_days": 60,
        "sort_order": 4
    },
    MilestoneKey.DESIGN_SURVEY: {
        "name": "全专业设计查勘",
        "phase": MilestonePhase.DESIGN,
        "duration_days": 30,
        "sort_order": 5
    },
    MilestoneKey.DESIGN_APPROVAL: {
        "name": "全专业设计批复/物资请购",
        "phase": MilestonePhase.DESIGN,
        "duration_days": 45,
        "sort_order": 6
    },
    MilestoneKey.MATERIALS_ARRIVAL: {
        "name": "物资到货",
        "phase": MilestonePhase.DESIGN,
        "duration_days": 45,
        "sort_order": 7
    },
    MilestoneKey.CONSTRUCTION: {
        "name": "施工建设",
        "phase": MilestonePhase.CONSTRUCTION,
        "duration_days": 0,
        "sort_order": 8
    },
    MilestoneKey.EXTERNAL_POWER: {
        "name": "外市电完工",
        "phase": MilestonePhase.FACILITY,
        "duration_days": 210,
        "sort_order": 9
    },
    MilestoneKey.DECORATION: {
        "name": "装修完成",
        "phase": MilestonePhase.FACILITY,
        "duration_days": 90,
        "sort_order": 10
    },
    MilestoneKey.EQUIPMENT_INSTALL: {
        "name": "配套完成及设备、动环安装",
        "phase": MilestonePhase.FACILITY,
        "duration_days": 120,
        "sort_order": 11
    },
    MilestoneKey.PIPELINE: {
        "name": "管道完成",
        "phase": MilestonePhase.FACILITY,
        "duration_days": 180,
        "sort_order": 12
    },
    MilestoneKey.CIRCUIT: {
        "name": "线路完成",
        "phase": MilestonePhase.FACILITY,
        "duration_days": 30,
        "sort_order": 13
    },
    MilestoneKey.COMPLETION: {
        "name": "建设完工",
        "phase": MilestonePhase.COMPLETION,
        "duration_days": 0,
        "sort_order": 14
    },
    MilestoneKey.GO_LIVE: {
        "name": "动环上线",
        "phase": MilestonePhase.COMPLETION,
        "duration_days": 30,
        "sort_order": 15
    },
}


class LifecycleMilestone(Base):
    """
    建设生命周期里程碑表 - 跟踪机房建设进度
    完全匹配机房建设周期流程
    """
    __tablename__ = "lifecycle_milestones"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    instance_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("instances.id", ondelete="CASCADE"), 
        nullable=False,
        comment="关联实例ID"
    )
    
    milestone_key = Column(
        SQLEnum(MilestoneKey), 
        nullable=False,
        comment="里程碑类型"
    )
    
    phase = Column(
        SQLEnum(MilestonePhase),
        nullable=False,
        comment="建设阶段"
    )
    
    milestone_name = Column(String(100), nullable=False, comment="里程碑名称")
    description = Column(String(500), nullable=True, comment="里程碑描述")
    
    planned_start_date = Column(Date, nullable=True, comment="计划开始日期")
    planned_end_date = Column(Date, nullable=True, comment="计划结束日期")
    actual_start_date = Column(Date, nullable=True, comment="实际开始日期")
    actual_end_date = Column(Date, nullable=True, comment="实际结束日期")
    
    duration_days = Column(Integer, default=0, comment="持续时间(天)")
    
    status = Column(
        SQLEnum(MilestoneStatus), 
        default=MilestoneStatus.PENDING,
        comment="状态: PENDING/ONGOING/COMPLETED/DELAYED/CANCELLED"
    )
    
    progress = Column(Integer, default=0, comment="进度百分比(0-100)")
    
    responsible_person = Column(String(100), nullable=True, comment="负责人")
    responsible_dept = Column(String(100), nullable=True, comment="责任部门")
    remarks = Column(String(500), nullable=True, comment="备注")
    
    sort_order = Column(Integer, default=0, comment="排序序号")
    
    is_critical_path = Column(Boolean, default=False, comment="是否关键路径")
    dependencies = Column(String(200), nullable=True, comment="依赖里程碑(逗号分隔)")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    instance = relationship("Instance", back_populates="milestones")
    
    __table_args__ = (
        Index('ix_lifecycle_milestones_instance_id', 'instance_id'),
        Index('ix_lifecycle_milestones_status', 'status'),
        Index('ix_lifecycle_milestones_milestone_key', 'milestone_key'),
        Index('ix_lifecycle_milestones_phase', 'phase'),
        Index('ix_lifecycle_milestones_planned_end_date', 'planned_end_date'),
    )
    
    def __repr__(self):
        return f"<LifecycleMilestone {self.milestone_key.value} ({self.status.value})>"
    
    @property
    def is_delayed(self):
        """判断是否延期"""
        from datetime import date
        if self.planned_end_date and self.status not in [MilestoneStatus.COMPLETED, MilestoneStatus.CANCELLED]:
            return date.today() > self.planned_end_date
        return False
    
    @property
    def delay_days(self):
        """计算延期天数"""
        from datetime import date
        if self.is_delayed:
            return (date.today() - self.planned_end_date).days
        return 0
    
    @property
    def phase_display(self):
        """阶段显示名称"""
        phase_map = {
            MilestonePhase.INITIATION: "立项阶段",
            MilestonePhase.PROCUREMENT: "采购阶段",
            MilestonePhase.DESIGN: "设计阶段",
            MilestonePhase.CONSTRUCTION: "施工建设",
            MilestonePhase.FACILITY: "配套设施",
            MilestonePhase.COMPLETION: "上线验收"
        }
        return phase_map.get(self.phase, "-")
    
    @classmethod
    def create_default_milestones(cls, instance_id):
        """为实例创建默认里程碑"""
        milestones = []
        for key, config in MILESTONE_CONFIG.items():
            milestone = cls(
                instance_id=instance_id,
                milestone_key=key,
                phase=config["phase"],
                milestone_name=config["name"],
                duration_days=config["duration_days"],
                sort_order=config["sort_order"],
                status=MilestoneStatus.PENDING
            )
            milestones.append(milestone)
        return milestones
