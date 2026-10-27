from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class SessionInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    usuario_id: PyObjectId
    dispositivo_id: str
    ip: str
    user_agent: Optional[str] = None
    refresh_token_hash: Optional[str] = None
    activa: bool = True
    creada_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ultimo_acceso: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expira_en: datetime

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }


class VerificationTokenInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    usuario_id: PyObjectId
    tipo: str  # otp_login, verificar_email, reset_password
    codigo_hash: str
    intentos: int = 0
    expira_en: datetime
    usado: bool = False
    creado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
