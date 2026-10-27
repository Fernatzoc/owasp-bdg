from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class RequestLineCreate(BaseModel):
    producto_id: str
    cant_solicitada: float = Field(..., gt=0)


class RequestLineResponse(BaseModel):
    producto_id: str
    codigo: str
    nombre: str
    cant_solicitada: float
    cant_confirmada: float = 0.0
    cant_recibida: float = 0.0
    recibido: bool = False
    motivo: Optional[str] = None


class RequestCreate(BaseModel):
    proveedor_id: str
    fecha_entrega: str  # YYYY-MM-DD
    observaciones: Optional[str] = ""
    lineas: List[RequestLineCreate] = Field(..., min_length=1)
    enviar: bool = False


class RequestUpdate(BaseModel):
    proveedor_id: Optional[str] = None
    fecha_entrega: Optional[str] = None
    observaciones: Optional[str] = None
    lineas: Optional[List[RequestLineCreate]] = None


class RequestCancelRequest(BaseModel):
    motivo: str = Field(..., min_length=3)


class RequestLineConfirm(BaseModel):
    producto_id: str
    cant_confirmada: float = Field(..., ge=0)


class RequestConfirmRequest(BaseModel):
    lineas: List[RequestLineConfirm] = Field(..., min_length=1)
    nueva_fecha_entrega: Optional[str] = None
    comentario: Optional[str] = None


class RequestRejectRequest(BaseModel):
    motivo: str = Field(..., min_length=3)


class RequestLineReceive(BaseModel):
    producto_id: str
    recibido: bool
    cant_recibida: float = Field(..., ge=0)
    motivo: Optional[str] = None  # Obligatorio si cant_recibida < cant_confirmada


class RequestReceiveRequest(BaseModel):
    lineas: List[RequestLineReceive] = Field(..., min_length=1)
    comentario: Optional[str] = None


class RequestCloseRequest(BaseModel):
    motivo: str = Field(..., min_length=3)


class RequestResponse(BaseModel):
    id: str
    numero: str
    proveedor_id: str
    nombre_proveedor: Optional[str] = None
    fecha_entrega: str
    estado: str
    observaciones: Optional[str] = ""
    creado_por: str
    nombre_creador: Optional[str] = None
    lineas: List[RequestLineResponse]
    creado_en: datetime
    actualizado_en: datetime
    es_confirmacion_parcial: bool = False
    total_lineas: int = 0
