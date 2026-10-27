from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROLES_VALIDOS, ROL_PROVEEDOR
from app.core.exceptions import AppException
from app.services.audit_service import record_audit_event


async def list_users(
    db: AsyncIOMotorDatabase,
    query: Optional[str] = None,
    rol: Optional[str] = None,
    estado: Optional[str] = None,
    page: int = 1,
    size: int = 20
) -> Dict[str, Any]:
    filtro: Dict[str, Any] = {}
    if query:
        filtro["$or"] = [
            {"nombre": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}}
        ]
    if rol:
        filtro["roles"] = rol
    if estado:
        filtro["estado"] = estado

    skip = (page - 1) * size
    total = await db.usuarios.count_documents(filtro)
    cursor = db.usuarios.find(filtro).sort("creado_en", -1).skip(skip).limit(size)
    usuarios = await cursor.to_list(length=size)

    items = []
    for u in usuarios:
        items.append({
            "id": str(u["_id"]),
            "nombre": u["nombre"],
            "email": u["email"],
            "roles": u.get("roles", []),
            "proveedor_id": str(u["proveedor_id"]) if u.get("proveedor_id") else None,
            "estado": u.get("estado", "activo"),
            "intentos_fallidos": u.get("intentos_fallidos", 0),
            "bloqueado_hasta": u.get("bloqueado_hasta"),
            "creado_en": u.get("creado_en")
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


async def get_user_by_id(db: AsyncIOMotorDatabase, user_id: str) -> Dict[str, Any]:
    if not ObjectId.is_valid(user_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de usuario inválido")

    u = await db.usuarios.find_one({"_id": ObjectId(user_id)})
    if not u:
        raise AppException(status_code=404, codigo="USUARIO_NO_ENCONTRADO", mensaje="Usuario no encontrado")

    return {
        "id": str(u["_id"]),
        "nombre": u["nombre"],
        "email": u["email"],
        "roles": u.get("roles", []),
        "proveedor_id": str(u["proveedor_id"]) if u.get("proveedor_id") else None,
        "estado": u.get("estado", "activo"),
        "intentos_fallidos": u.get("intentos_fallidos", 0),
        "bloqueado_hasta": u.get("bloqueado_hasta"),
        "creado_en": u.get("creado_en")
    }


async def update_user_roles(
    db: AsyncIOMotorDatabase,
    user_id: str,
    roles: List[str],
    proveedor_id: Optional[str],
    admin_id: str,
    ip: str
) -> Dict[str, Any]:
    if not ObjectId.is_valid(user_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de usuario inválido")

    # Validar roles
    for r in roles:
        if r not in ROLES_VALIDOS:
            raise AppException(status_code=400, codigo="ROL_INVALIDO", mensaje=f"El rol '{r}' no es válido")

    if not roles:
        raise AppException(status_code=400, codigo="ROLES_VACIOS", mensaje="El usuario debe tener al menos un rol")

    update_fields: Dict[str, Any] = {"roles": roles}

    # Si incluye rol Proveedor, vincular o validar proveedor_id
    if ROL_PROVEEDOR in roles:
        if not proveedor_id or not ObjectId.is_valid(proveedor_id):
            raise AppException(
                status_code=400,
                codigo="PROVEEDOR_REQUERIDO",
                mensaje="Debe vincular un proveedor al asignar el rol Proveedor"
            )
        prov = await db.proveedores.find_one({"_id": ObjectId(proveedor_id)})
        if not prov:
            raise AppException(status_code=404, codigo="PROVEEDOR_NO_EXISTE", mensaje="Proveedor no encontrado")
        update_fields["proveedor_id"] = ObjectId(proveedor_id)
    else:
        update_fields["proveedor_id"] = None

    res = await db.usuarios.update_one({"_id": ObjectId(user_id)}, {"$set": update_fields})
    if res.matched_count == 0:
        raise AppException(status_code=404, codigo="USUARIO_NO_ENCONTRADO", mensaje="Usuario no encontrado")

    await record_audit_event(
        db=db,
        evento="ROLES_MODIFICADOS",
        ip=ip,
        exito=True,
        usuario_id=admin_id,
        detalle=f"Se actualizaron los roles del usuario {user_id} a: {roles}"
    )

    return await get_user_by_id(db, user_id)


async def update_user_status(
    db: AsyncIOMotorDatabase,
    user_id: str,
    nuevo_estado: str,
    admin_id: str,
    ip: str
) -> Dict[str, Any]:
    if not ObjectId.is_valid(user_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de usuario inválido")

    if nuevo_estado not in ["activo", "inactivo", "bloqueado"]:
        raise AppException(status_code=400, codigo="ESTADO_INVALIDO", mensaje="Estado no permitido")

    update_doc: Dict[str, Any] = {"estado": nuevo_estado}
    if nuevo_estado == "activo":
        update_doc["intentos_fallidos"] = 0
        update_doc["bloqueado_hasta"] = None

    res = await db.usuarios.update_one({"_id": ObjectId(user_id)}, {"$set": update_doc})
    if res.matched_count == 0:
        raise AppException(status_code=404, codigo="USUARIO_NO_ENCONTRADO", mensaje="Usuario no encontrado")

    # Si se desactiva o bloquea, cerrar todas sus sesiones activas
    if nuevo_estado in ["inactivo", "bloqueado"]:
        await db.sesiones.update_many(
            {"usuario_id": ObjectId(user_id), "activa": True},
            {"$set": {"activa": False}}
        )

    await record_audit_event(
        db=db,
        evento="ESTADO_USUARIO_MODIFICADO",
        ip=ip,
        exito=True,
        usuario_id=admin_id,
        detalle=f"Se cambió el estado del usuario {user_id} a '{nuevo_estado}'"
    )

    return await get_user_by_id(db, user_id)


async def force_user_logout(
    db: AsyncIOMotorDatabase,
    user_id: str,
    admin_id: str,
    ip: str
) -> Dict[str, Any]:
    if not ObjectId.is_valid(user_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de usuario inválido")

    res = await db.sesiones.update_many(
        {"usuario_id": ObjectId(user_id), "activa": True},
        {"$set": {"activa": False}}
    )

    await record_audit_event(
        db=db,
        evento="SESION_FORZADA_CERRADA",
        ip=ip,
        exito=True,
        usuario_id=admin_id,
        detalle=f"Administrador forzó cierre de sesiones ({res.modified_count}) para el usuario {user_id}"
    )

    return {
        "mensaje": f"Se cerraron {res.modified_count} sesión(es) activa(s) del usuario",
        "sesiones_cerradas": res.modified_count
    }
