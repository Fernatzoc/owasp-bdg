from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class MovementInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    tipo: str  # PEDIDO_CREADO, ESTADO_CAMBIADO, CONFIRMACION, INGRESO_INVENTARIO
    solicitud_id: PyObjectId
    producto_id: Optional[PyObjectId] = None
    codigo_producto: Optional[str] = None
    nombre_producto: Optional[str] = None
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    cantidad: Optional[float] = None
    usuario_id: PyObjectId
    comentario: Optional[str] = None
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
