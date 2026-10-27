from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN
from app.core.database import get_database
from app.core.dependencies import get_client_ip, require_roles
from app.schemas.user import UserResponse, UserUpdateRolesRequest, UserUpdateStatusRequest
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Usuarios y Roles"])


@router.get("", summary="Listar usuarios (solo Administrador)")
async def list_users(
    query: Optional[str] = None,
    rol: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await user_service.list_users(db, query, rol, estado, page, size)


@router.get("/{id}", response_model=UserResponse, summary="Obtener detalle de usuario")
async def get_user(
    id: str,
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    return await user_service.get_user_by_id(db, id)


@router.patch("/{id}", response_model=UserResponse, summary="Actualizar estado del usuario (activo/inactivo/bloqueado)")
async def update_user_status(
    id: str,
    data: UserUpdateStatusRequest,
    request: Request,
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await user_service.update_user_status(
        db=db,
        user_id=id,
        nuevo_estado=data.estado,
        admin_id=str(current_admin["_id"]),
        ip=ip
    )


@router.patch("/{id}/roles", response_model=UserResponse, summary="Asignar o modificar roles de un usuario")
async def update_user_roles(
    id: str,
    data: UserUpdateRolesRequest,
    request: Request,
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await user_service.update_user_roles(
        db=db,
        user_id=id,
        roles=data.roles,
        proveedor_id=data.proveedor_id,
        admin_id=str(current_admin["_id"]),
        ip=ip
    )


@router.post("/{id}/force-logout", summary="Forzar cierre de sesión de un usuario")
async def force_user_logout(
    id: str,
    request: Request,
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await user_service.force_user_logout(
        db=db,
        user_id=id,
        admin_id=str(current_admin["_id"]),
        ip=ip
    )
