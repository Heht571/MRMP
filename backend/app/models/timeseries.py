import uuid
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, DateTime, Index, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.database import Base


class TimeseriesData(Base):
    """时序数据表 - 存储实例的时序属性值

    采用 ref_id 引用方式，与主数据库解耦:
    - ref_id 格式: "ts:{attribute_name}:{instance_id}"
    - 主数据库 instances 表的 data 字段中存储 {"__ts_ref__": "ts:cpu:instance_id"}

    支持多指标时序数据:
    {
        "cpu": 45.5,
        "memory": 1024,
        "disk": 50.2
    }
    """
    __tablename__ = "timeseries_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    ref_id = Column(
        String(200),
        nullable=False,
        unique=True,
        comment="时序数据引用ID，格式: ts:{属性名}:{instance_id}"
    )

    instance_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        comment="关联实例ID (冗余字段，便于查询)"
    )

    attribute_name = Column(
        String(100),
        nullable=False,
        comment="时序属性名"
    )

    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="时间戳"
    )

    value = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="时序值对象 (支持多指标: {cpu: 45.5, memory: 1024})"
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_timeseries_ref_id', 'ref_id', unique=True),
        Index('ix_timeseries_instance_id', 'instance_id'),
        Index('ix_timeseries_attribute_name', 'attribute_name'),
        Index('ix_timeseries_timestamp', 'timestamp'),
        Index('ix_timeseries_compound', 'instance_id', 'attribute_name', 'timestamp'),
    )

    def __repr__(self):
        return f"<TimeseriesData ref={self.ref_id} time={self.timestamp}>"

    @staticmethod
    def generate_ref_id(instance_id: uuid.UUID, attribute_name: str) -> str:
        """生成 ref_id"""
        return f"ts:{attribute_name}:{str(instance_id)}"