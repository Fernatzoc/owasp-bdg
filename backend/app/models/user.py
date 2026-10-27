from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.common import PyObjectId


class RoleInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    nombre: str
    descripcion: str
    permisos: List[str] = Field(default_factory=list)


class UserInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    nombre: str
    email: EmailStr
    password_hash: str
    roles: List[str] = Field(default_factory=lambda: ["Consulta"])
    proveedor_id: Optional[PyObjectId] = None
    estado: str = "pendiente"  # pendiente, activo, bloqueado, inactivo
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None
    historial_passwords: List[str] = Field(default_factory=list)
    creado_en: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
