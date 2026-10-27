from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.common import PyObjectId


class SupplierInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    codigo: str
    nombre: str
    nit: str
    email: EmailStr
    telefono: Optional[str] = ""
    activo: bool = True

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
