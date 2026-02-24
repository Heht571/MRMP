from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Literal
from datetime import datetime


class InstanceBase(BaseModel):
    name: str = Field(..., max_length=200)
    model_id: int
    attributes: Dict[str, Any] = Field(default_factory=dict)
    status: Literal["planning", "construction", "active", "retired"] = "planning"
    room_type: Optional[Literal["important", "normal", "business"]] = None
    evolution_type: Optional[Literal["target", "anchor"]] = None


class InstanceCreate(InstanceBase):
    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, v):
        return v or {}


class InstanceUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    attributes: Optional[Dict[str, Any]] = None
    status: Optional[Literal["planning", "construction", "active", "retired"]] = None
    room_type: Optional[Literal["important", "normal", "business"]] = None
    evolution_type: Optional[Literal["target", "anchor"]] = None


class InstanceResponse(InstanceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
