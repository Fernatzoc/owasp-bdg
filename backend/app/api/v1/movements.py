from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN, ROL_COMPRAS, ROL_PROVEEDOR, ROL_BODEGA, ROL_CONSULTA
from app.core.database import get_database
from app.core.dependencies import require_roles
from app.services import movement_service

router = APIRouter(prefix="/movements", tags=["Consulta de Movimientos"])


@router.get("", summary="Consulta de movimientos (Pestañas: pedidos, ingresos, cambios)")
async def get_movements(
    tipo: str = Query(..., regex="^(pedidos|ingresos|cambios)$"),
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    producto_id: Optional[str] = None,
    numero_solicitud: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_roles(ROL_CONSULTA, ROL_COMPRAS, ROL_PROVEEDOR, ROL_BODEGA, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await movement_service.query_movements(
        db=db,
        tipo=tipo,
        user=current_user,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        proveedor_id=proveedor_id,
        producto_id=producto_id,
        numero_solicitud=numero_solicitud,
        page=page,
        size=size
    )
