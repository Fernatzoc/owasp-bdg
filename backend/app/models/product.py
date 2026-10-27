from typing import Optional
from pydantic import BaseModel, Field
from app.models.common import PyObjectId


class ProductInDB(BaseModel):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    codigo: str
    nombre: str
    descripcion: Optional[str] = ""
    unidad: str = "unidad"
    activo: bool = True

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }
