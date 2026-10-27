from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from app.core.config import ROL_ADMIN, ROL_COMPRAS, ROL_PROVEEDOR, ROL_BODEGA
from app.core.database import get_database, get_client
from app.core.dependencies import require_roles
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestCancelRequest,
    RequestConfirmRequest,
    RequestRejectRequest,
    RequestReceiveRequest,
    RequestCloseRequest,
    RequestResponse
)
from app.services import request_service

router = APIRouter(prefix="/requests", tags=["Gestión de Solicitudes"])


@router.get("", summary="Listar solicitudes de compra")
async def list_requests(
    estado: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    numero: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_PROVEEDOR, ROL_ADMIN, ROL_BODEGA)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.list_requests(
        db=db,
        user=current_user,
        estado=estado,
        proveedor_id=proveedor_id,
        numero=numero,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        page=page,
        size=size
    )


@router.get("/{id}", response_model=RequestResponse, summary="Obtener detalle de solicitud")
async def get_request(
    id: str,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_PROVEEDOR, ROL_BODEGA, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.get_request_by_id(db, id, current_user)


@router.post("", response_model=RequestResponse, summary="Crear solicitud (Borrador o Enviada)")
async def create_request(
    data: RequestCreate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.create_request(db, data, current_user)


@router.patch("/{id}", response_model=RequestResponse, summary="Modificar solicitud en Borrador")
async def update_request(
    id: str,
    data: RequestUpdate,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.update_draft_request(db, id, data, current_user)


@router.post("/{id}/send", response_model=RequestResponse, summary="Enviar solicitud al proveedor")
async def send_request(
    id: str,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.send_request_to_supplier(db, id, current_user)


@router.post("/{id}/cancel", response_model=RequestResponse, summary="Cancelar solicitud con motivo")
async def cancel_request(
    id: str,
    data: RequestCancelRequest,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.cancel_request(db, id, data.motivo, current_user)


@router.post("/{id}/confirm", response_model=RequestResponse, summary="Confirmar cantidades por línea (Proveedor)")
async def confirm_request(
    id: str,
    data: RequestConfirmRequest,
    current_user=Depends(require_roles(ROL_PROVEEDOR, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.confirm_supplier_request(db, id, data, current_user)


@router.post("/{id}/reject", response_model=RequestResponse, summary="Rechazar solicitud con motivo (Proveedor)")
async def reject_request(
    id: str,
    data: RequestRejectRequest,
    current_user=Depends(require_roles(ROL_PROVEEDOR, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.reject_supplier_request(db, id, data.motivo, current_user)


@router.post("/{id}/receive", response_model=RequestResponse, summary="Registrar recepción de entrega e inventario (Bodega)")
async def receive_delivery(
    id: str,
    data: RequestReceiveRequest,
    current_user=Depends(require_roles(ROL_BODEGA, ROL_ADMIN)),
    client: AsyncIOMotorClient = Depends(get_client),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.receive_delivery(
        client=client,
        db=db,
        req_id=id,
        data=data,
        user=current_user
    )


@router.post("/{id}/close", response_model=RequestResponse, summary="Cerrar solicitud con faltante (Compras)")
async def close_request(
    id: str,
    data: RequestCloseRequest,
    current_user=Depends(require_roles(ROL_COMPRAS, ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await request_service.close_request_with_shortage(db, id, data.motivo, current_user)
