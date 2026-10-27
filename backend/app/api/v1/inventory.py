from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN, ROL_COMPRAS, ROL_BODEGA, ROL_CONSULTA
from app.core.database import get_database
from app.core.dependencies import require_roles
from app.services import inventory_service

router = APIRouter(prefix="/inventory", tags=["Consulta de Inventario"])


@router.get("", summary="Consulta de inventario disponible")
async def get_inventory(
    query: Optional[str] = None,
    sort_by: str = Query("codigo", regex="^(codigo|nombre|cantidad|actualizado_en)$"),
    sort_order: int = Query(1, ge=-1, le=1),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_roles(ROL_CONSULTA, ROL_BODEGA, ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await inventory_service.list_inventory(
        db=db,
        query=query,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        size=size
    )


@router.get("/export", summary="Exportar inventario a formato CSV")
async def export_inventory(
    current_user=Depends(require_roles(ROL_CONSULTA, ROL_BODEGA, ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    csv_content = await inventory_service.export_inventory_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventario_actual.csv"}
    )
