from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class SecurityAuditInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    evento: str  # LOGIN_EXITOSO, LOGIN_FALLIDO, OTP_ENVIADO, PASSWORD_CAMBIADA, ROLES_MODIFICADOS, SESION_FORZADA_CERRADA, etc.
    usuario_id: Optional[PyObjectId] = None
    email: Optional[str] = None
    ip: str
    dispositivo_id: Optional[str] = None
    exito: bool
    detalle: Optional[str] = ""
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
