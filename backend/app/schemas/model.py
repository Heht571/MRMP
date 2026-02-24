from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ModelBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    category: str = Field(..., max_length=50)


class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    attributes: Optional[Dict[str, Any]] = None


class ModelResponse(ModelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
