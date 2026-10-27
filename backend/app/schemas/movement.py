from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MovementResponse(BaseModel):
    id: str
    tipo: str  # PEDIDO_CREADO, ESTADO_CAMBIADO, CONFIRMACION, INGRESO_INVENTARIO
    solicitud_id: str
    numero_solicitud: Optional[str] = None
    producto_id: Optional[str] = None
    codigo_producto: Optional[str] = None
    nombre_producto: Optional[str] = None
    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    cantidad: Optional[float] = None
    usuario_id: str
    nombre_usuario: Optional[str] = None
    comentario: Optional[str] = None
    fecha: datetime
