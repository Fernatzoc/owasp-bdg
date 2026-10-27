from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class SupplierCreate(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=150)
    nit: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    telefono: Optional[str] = ""
    activo: bool = True


class SupplierUpdate(BaseModel):
    nombre: Optional[str] = None
    nit: Optional[str] = None
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class SupplierResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    nit: str
    email: EmailStr
    telefono: Optional[str] = ""
    activo: bool
