from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Dict, Any
from bson import ObjectId
from fastapi import Depends, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings, PERMISOS_POR_ROL, ROL_ADMIN
from app.core.database import get_database
from app.core.exceptions import AppException
from app.core.security import decode_token

security_bearer = HTTPBearer(auto_error=False)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def get_device_id(request: Request) -> str:
    # Intenta leer de cookie HttpOnly o del header X-Device-Id
    device_id = request.cookies.get("dispositivo_id") or request.headers.get("X-Device-Id")
    if not device_id:
        return "dispositivo_desconocido"
    return device_id


async def get_current_user_and_session(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    # Buscar token en Authorization header o cookie
    token = None
    if auth and auth.credentials:
        token = auth.credentials
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token")

    if not token:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="NO_AUTORIZADO",
            mensaje="Token de autenticación no proporcionado"
        )

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="TOKEN_INVALIDO",
            mensaje="Tipo de token inválido"
        )

    user_id_str = payload.get("sub")
    session_id_str = payload.get("session_id")

    if not user_id_str or not session_id_str:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="TOKEN_INVALIDO",
            mensaje="Token sin información requerida de usuario o sesión"
        )

    try:
        user_id = ObjectId(user_id_str)
        session_id = ObjectId(session_id_str)
    except Exception:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="TOKEN_INVALIDO",
            mensaje="Identificadores de token malformados"
        )

    # Validar sesión única y activa en base de datos (RF-SEG-06)
    session = await db.sesiones.find_one({"_id": session_id})
    now = datetime.now(timezone.utc)

    if not session or not session.get("activa", False):
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="SESION_INVALIDADA",
            mensaje="Su sesión fue cerrada porque se inició en otro equipo o ha expirado"
        )

    expira_en = session.get("expira_en")
    if expira_en:
        if expira_en.tzinfo is None:
            expira_en = expira_en.replace(tzinfo=timezone.utc)
        if expira_en < now:
            await db.sesiones.update_one({"_id": session_id}, {"$set": {"activa": False}})
            raise AppException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                codigo="SESION_INVALIDADA",
                mensaje="Su sesión ha expirado por inactividad"
            )

    # Renovación deslizante por actividad (30 minutos)
    nueva_expiracion = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    await db.sesiones.update_one(
        {"_id": session_id},
        {"$set": {"ultimo_acceso": now, "expira_en": nueva_expiracion}}
    )

    # Validar usuario
    user = await db.usuarios.find_one({"_id": user_id})
    if not user:
        raise AppException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            codigo="USUARIO_NO_EXISTE",
            mensaje="El usuario no existe"
        )

    if user.get("estado") != "activo":
        raise AppException(
            status_code=status.HTTP_403_FORBIDDEN,
            codigo="USUARIO_INACTIVO",
            mensaje=f"La cuenta del usuario se encuentra en estado '{user.get('estado')}'"
        )

    return user, session


async def get_current_user(
    auth_data: Tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_current_user_and_session)
) -> Dict[str, Any]:
    user, _ = auth_data
    return user


async def get_current_session(
    auth_data: Tuple[Dict[str, Any], Dict[str, Any]] = Depends(get_current_user_and_session)
) -> Dict[str, Any]:
    _, session = auth_data
    return session


def require_roles(*allowed_roles: str):
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = user.get("roles", [])
        # Administrador tiene acceso total
        if ROL_ADMIN in user_roles:
            return user

        if not any(role in allowed_roles for role in user_roles):
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                codigo="ACCESO_DENEGADO",
                mensaje="No cuenta con el rol necesario para realizar esta acción"
            )
        return user
    return role_checker


def require_permissions(*required_permissions: str):
    async def permission_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = user.get("roles", [])
        if ROL_ADMIN in user_roles:
            return user

        # Agrupar todos los permisos de todos los roles del usuario
        user_permissions = set()
        for role in user_roles:
            for p in PERMISOS_POR_ROL.get(role, []):
                user_permissions.add(p)

        if not all(p in user_permissions for p in required_permissions):
            raise AppException(
                status_code=status.HTTP_403_FORBIDDEN,
                codigo="ACCESO_DENEGADO",
                mensaje="No cuenta con los permisos necesarios para realizar esta acción"
            )
        return user
    return permission_checker
