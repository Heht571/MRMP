from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class RelationBase(BaseModel):
    source_id: int
    target_id: int
    relation_type: Literal["contain", "connect", "carry", "associate"]
    attributes: Dict[str, Any] = Field(default_factory=dict)


class RelationCreate(RelationBase):
    pass


class RelationResponse(RelationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
