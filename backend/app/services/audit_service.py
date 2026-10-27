from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase


async def record_audit_event(
    db: AsyncIOMotorDatabase,
    evento: str,
    ip: str,
    exito: bool,
    usuario_id: Optional[str] = None,
    email: Optional[str] = None,
    dispositivo_id: Optional[str] = None,
    detalle: Optional[str] = ""
) -> None:
    """Registra un evento auditable en la bitácora de seguridad."""
    u_id = ObjectId(usuario_id) if usuario_id and ObjectId.is_valid(usuario_id) else None
    doc = {
        "evento": evento,
        "usuario_id": u_id,
        "email": email,
        "ip": ip,
        "dispositivo_id": dispositivo_id,
        "exito": exito,
        "detalle": detalle,
        "fecha": datetime.now(timezone.utc)
    }
    await db.bitacora_seguridad.insert_one(doc)
