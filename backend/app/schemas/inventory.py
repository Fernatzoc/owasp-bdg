from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class InventoryResponse(BaseModel):
    id: str
    producto_id: str
    codigo: str
    nombre: str
    unidad: Optional[str] = "unidad"
    cantidad: float
    actualizado_en: datetime
