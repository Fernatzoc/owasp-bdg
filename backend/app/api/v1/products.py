from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN, ROL_COMPRAS, ROL_BODEGA, ROL_CONSULTA
from app.core.database import get_database
from app.core.dependencies import require_roles
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services import catalog_service

router = APIRouter(prefix="/products", tags=["Catálogo de Productos"])


@router.get("", summary="Listar productos con filtros y paginación")
async def list_products(
    query: Optional[str] = None,
    activo: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_roles(ROL_CONSULTA, ROL_COMPRAS, ROL_BODEGA, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.list_products(db, query, activo, page, size)


@router.get("/{id}", response_model=ProductResponse, summary="Obtener producto por ID")
async def get_product(
    id: str,
    current_user=Depends(require_roles(ROL_CONSULTA, ROL_COMPRAS, ROL_BODEGA, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.get_product_by_id(db, id)


@router.post("", response_model=ProductResponse, summary="Crear un nuevo producto")
async def create_product(
    data: ProductCreate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.create_product(db, data)


@router.patch("/{id}", response_model=ProductResponse, summary="Actualizar producto")
async def update_product(
    id: str,
    data: ProductUpdate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await catalog_service.update_product(db, id, data)
