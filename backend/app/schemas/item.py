from pydantic import BaseModel, ConfigDict, field_serializer
from typing import Optional
from datetime import datetime


class ItemBase(BaseModel):
    name: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ItemRead(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer('created_at', 'updated_at')
    def serialize_dt(self, dt: datetime) -> str:
        return dt.isoformat()
