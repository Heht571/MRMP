import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class ImportHistory(Base):
    """导入历史记录"""
    __tablename__ = "import_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_id = Column(UUID(as_uuid=True), ForeignKey("models.id", ondelete="CASCADE"), nullable=False, comment="模型ID")
    file_name = Column(String(255), nullable=True, comment="导入文件名")
    file_size = Column(Integer, nullable=True, comment="文件大小(字节)")
    total_rows = Column(Integer, default=0, comment="总行数")
    created_count = Column(Integer, default=0, comment="新增数量")
    updated_count = Column(Integer, default=0, comment="更新数量")
    deleted_count = Column(Integer, default=0, comment="删除数量")
    skipped_count = Column(Integer, default=0, comment="跳过数量")
    error_count = Column(Integer, default=0, comment="错误数量")
    errors = Column(JSONB, nullable=True, comment="错误详情列表")
    import_mode = Column(String(50), default="upsert", comment="导入模式")
    status = Column(String(20), default="pending", comment="状态: pending/processing/completed/failed")
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="开始时间")
    finished_at = Column(DateTime(timezone=True), nullable=True, comment="结束时间")
    created_by = Column(String(100), nullable=True, comment="操作人")
    
    model = relationship("ModelV2", backref="import_histories")
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "model_id": str(self.model_id),
            "file_name": self.file_name,
            "file_size": self.file_size,
            "total_rows": self.total_rows,
            "created_count": self.created_count,
            "updated_count": self.updated_count,
            "deleted_count": self.deleted_count,
            "skipped_count": self.skipped_count,
            "error_count": self.error_count,
            "errors": self.errors,
            "import_mode": self.import_mode,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "created_by": self.created_by,
        }
