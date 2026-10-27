from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN, ROL_COMPRAS
from app.core.database import get_database
from app.core.dependencies import require_roles
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.services import catalog_service

router = APIRouter(prefix="/suppliers", tags=["Catálogo de Proveedores"])


@router.get("", summary="Listar proveedores con filtros y paginación")
async def list_suppliers(
    query: Optional[str] = None,
    activo: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.list_suppliers(db, query, activo, page, size)


@router.get("/{id}", response_model=SupplierResponse, summary="Obtener proveedor por ID")
async def get_supplier(
    id: str,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.get_supplier_by_id(db, id)


@router.post("", response_model=SupplierResponse, summary="Crear nuevo proveedor")
async def create_supplier(
    data: SupplierCreate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.create_supplier(db, data)


@router.patch("/{id}", response_model=SupplierResponse, summary="Actualizar proveedor")
async def update_supplier(
    id: str,
    data: SupplierUpdate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.update_supplier(db, id, data)
