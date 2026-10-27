from typing import Optional
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=150)
    descripcion: Optional[str] = ""
    unidad: str = Field(default="unidad", max_length=50)
    activo: bool = True


class ProductUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    unidad: Optional[str] = None
    activo: Optional[bool] = None


class ProductResponse(BaseModel):
    id: str
    codigo: str
    nombre: str
    descripcion: Optional[str] = ""
    unidad: str
    activo: bool
