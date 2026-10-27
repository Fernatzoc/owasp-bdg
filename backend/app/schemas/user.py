from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: str
    nombre: str
    email: EmailStr
    roles: List[str]
    proveedor_id: Optional[str] = None
    estado: str
    creado_en: datetime
    intentos_fallidos: int = 0
    bloqueado_hasta: Optional[datetime] = None


class UserUpdateRolesRequest(BaseModel):
    roles: List[str]
    proveedor_id: Optional[str] = None


class UserUpdateStatusRequest(BaseModel):
    estado: str  # activo, inactivo, bloqueado
