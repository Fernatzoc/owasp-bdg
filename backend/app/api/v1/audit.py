from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN
from app.core.database import get_database
from app.core.dependencies import require_roles

router = APIRouter(prefix="/audit", tags=["Bitácora de Seguridad"])


@router.get("/security", summary="Consultar bitácora de eventos de seguridad (solo Administrador)")
async def get_security_audit(
    evento: Optional[str] = None,
    email: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    current_admin=Depends(require_roles(ROL_ADMIN)),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    filtro = {}
    if evento:
        filtro["evento"] = evento
    if email:
        filtro["email"] = {"$regex": email, "$options": "i"}

    skip = (page - 1) * size
    total = await db.bitacora_seguridad.count_documents(filtro)
    cursor = db.bitacora_seguridad.find(filtro).sort("fecha", -1).skip(skip).limit(size)
    docs = await cursor.to_list(length=size)

    items = []
    for d in docs:
        items.append({
            "id": str(d["_id"]),
            "evento": d.get("evento"),
            "usuario_id": str(d.get("usuario_id")) if d.get("usuario_id") else None,
            "email": d.get("email"),
            "ip": d.get("ip"),
            "dispositivo_id": d.get("dispositivo_id"),
            "exito": d.get("exito"),
            "detalle": d.get("detalle", ""),
            "fecha": d.get("fecha")
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }
