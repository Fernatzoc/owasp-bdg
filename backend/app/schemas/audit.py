from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SecurityAuditResponse(BaseModel):
    id: str
    evento: str
    usuario_id: Optional[str] = None
    email: Optional[str] = None
    ip: str
    dispositivo_id: Optional[str] = None
    exito: bool
    detalle: Optional[str] = ""
    fecha: datetime
