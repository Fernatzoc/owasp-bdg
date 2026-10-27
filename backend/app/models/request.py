from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class RequestLine(BaseModel):
    producto_id: PyObjectId
    codigo: str
    nombre: str
    cant_solicitada: float
    cant_confirmada: float = 0.0
    cant_recibida: float = 0.0
    recibido: bool = False
    motivo: Optional[str] = None  # faltante, dañado, producto incorrecto, otro


class RequestInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    numero: str  # Ej. SOL-2026-000001
    proveedor_id: PyObjectId
    fecha_entrega: str  # ISO string YYYY-MM-DD
    estado: str = "Borrador"  # Borrador, Enviada, Rechazada, Por entregar, Entregada, Entregada parcial, Cerrada con faltante, Cancelada
    observaciones: Optional[str] = ""
    creado_por: PyObjectId
    lineas: List[RequestLine] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actualizado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
