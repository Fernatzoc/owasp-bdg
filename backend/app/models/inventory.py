from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class InventoryInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    producto_id: PyObjectId
    codigo: str
    nombre: str
    cantidad: float = 0.0
    actualizado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
