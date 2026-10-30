from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from app.core.config import ROL_ADMIN, ROL_PROVEEDOR, ROL_COMPRAS, ROL_BODEGA
from app.core.exceptions import AppException
from app.services.email_service import send_request_notification_email
from app.schemas.request import (
    RequestCreate,
    RequestUpdate,
    RequestConfirmRequest,
    RequestReceiveRequest
)


ESTADOS_FINALES = ["Entregada", "Cerrada con faltante", "Rechazada", "Cancelada"]


async def generate_request_number(db: AsyncIOMotorDatabase) -> str:
    year = datetime.now().year
    prefix = f"SOL-{year}-"
    # Buscar el número más alto existente para este año
    ultimo = await db.solicitudes.find(
        {"numero": {"$regex": f"^{prefix}"}},
        {"numero": 1}
    ).sort("numero", -1).limit(1).to_list(length=1)

    if ultimo and "numero" in ultimo[0]:
        try:
            ultimo_num_str = ultimo[0]["numero"].replace(prefix, "")
            consecutivo = int(ultimo_num_str) + 1
        except Exception:
            consecutivo = 1
    else:
        consecutivo = 1

    return f"{prefix}{consecutivo:06d}"


async def enrich_request_doc(db: AsyncIOMotorDatabase, req: Dict[str, Any]) -> Dict[str, Any]:
    prov_id = req.get("proveedor_id")
    nombre_proveedor = "Desconocido"
    if prov_id:
        prov = await db.proveedores.find_one({"_id": prov_id})
        if prov:
            nombre_proveedor = prov.get("nombre", "Desconocido")

    creador_id = req.get("creado_por")
    nombre_creador = "Desconocido"
    if creador_id:
        u = await db.usuarios.find_one({"_id": creador_id})
        if u:
            nombre_creador = u.get("nombre", "Desconocido")

    # Evaluar si es confirmación parcial
    lineas = req.get("lineas", [])
    es_parcial = False
    if req.get("estado") in ["Por entregar", "Entregada parcial"]:
        for l in lineas:
            if l.get("cant_confirmada", 0) < l.get("cant_solicitada", 0):
                es_parcial = True
                break

    return {
        "id": str(req["_id"]),
        "numero": req.get("numero", ""),
        "proveedor_id": str(req["proveedor_id"]),
        "nombre_proveedor": nombre_proveedor,
        "fecha_entrega": req.get("fecha_entrega", ""),
        "estado": req.get("estado", "Borrador"),
        "observaciones": req.get("observaciones", ""),
        "creado_por": str(req.get("creado_por")),
        "nombre_creador": nombre_creador,
        "lineas": [
            {
                "producto_id": str(l["producto_id"]),
                "codigo": l.get("codigo", ""),
                "nombre": l.get("nombre", ""),
                "cant_solicitada": float(l.get("cant_solicitada", 0)),
                "cant_confirmada": float(l.get("cant_confirmada", 0)),
                "cant_recibida": float(l.get("cant_recibida", 0)),
                "recibido": bool(l.get("recibido", False)),
                "motivo": l.get("motivo")
            }
            for l in lineas
        ],
        "creado_en": req.get("creado_en"),
        "actualizado_en": req.get("actualizado_en"),
        "es_confirmacion_parcial": es_parcial,
        "total_lineas": len(lineas)
    }


async def list_requests(
    db: AsyncIOMotorDatabase,
    user: Dict[str, Any],
    estado: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    numero: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    page: int = 1,
    size: int = 50
) -> Dict[str, Any]:
    filtro: Dict[str, Any] = {}

    # Rol Proveedor solo puede ver sus solicitudes (RF-SEG y Sección 3)
    user_roles = user.get("roles", [])
    if ROL_PROVEEDOR in user_roles and ROL_ADMIN not in user_roles:
        prov_id = user.get("proveedor_id")
        if not prov_id:
            return {"items": [], "total": 0, "page": page, "size": size, "pages": 1}
        filtro["proveedor_id"] = ObjectId(prov_id)
        # Proveedores no ven borradores
        filtro["estado"] = {"$ne": "Borrador"}
    elif proveedor_id and ObjectId.is_valid(proveedor_id):
        filtro["proveedor_id"] = ObjectId(proveedor_id)

    if estado:
        filtro["estado"] = estado
    if numero:
        filtro["numero"] = {"$regex": numero, "$options": "i"}
    if fecha_desde or fecha_hasta:
        filtro_fecha = {}
        if fecha_desde:
            filtro_fecha["$gte"] = fecha_desde
        if fecha_hasta:
            filtro_fecha["$lte"] = fecha_hasta
        filtro["fecha_entrega"] = filtro_fecha

    skip = (page - 1) * size
    total = await db.solicitudes.count_documents(filtro)
    cursor = db.solicitudes.find(filtro).sort("creado_en", -1).skip(skip).limit(size)
    docs = await cursor.to_list(length=size)

    items = []
    for d in docs:
        items.append(await enrich_request_doc(db, d))

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


async def get_request_by_id(db: AsyncIOMotorDatabase, req_id: str, user: Dict[str, Any]) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    # Si es proveedor, solo ver sus solicitudes
    user_roles = user.get("roles", [])
    if ROL_PROVEEDOR in user_roles and ROL_ADMIN not in user_roles:
        if str(req.get("proveedor_id")) != str(user.get("proveedor_id")):
            raise AppException(status_code=403, codigo="ACCESO_DENEGADO", mensaje="No tiene acceso a esta solicitud")

    return await enrich_request_doc(db, req)


async def create_request(
    db: AsyncIOMotorDatabase,
    data: RequestCreate,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    # 1. Validar proveedor activo
    if not ObjectId.is_valid(data.proveedor_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de proveedor inválido")
    prov = await db.proveedores.find_one({"_id": ObjectId(data.proveedor_id), "activo": True})
    if not prov:
        raise AppException(status_code=400, codigo="PROVEEDOR_INVALIDO", mensaje="Proveedor no encontrado o inactivo")

    # 2. Validar fecha de entrega no anterior a hoy (RF-NEG-02)
    try:
        f_entrega = date.fromisoformat(data.fecha_entrega)
        if f_entrega < date.today():
            raise AppException(
                status_code=400,
                codigo="FECHA_INVALIDA",
                mensaje="La fecha de entrega no puede ser anterior al día de hoy"
            )
    except ValueError:
        raise AppException(status_code=400, codigo="FORMATO_FECHA_INVALIDO", mensaje="Formato de fecha inválido (YYYY-MM-DD)")

    # 3. Validar líneas: producto existente y no repetido
    productos_vistos = set()
    lineas_db = []
    for l in data.lineas:
        if not ObjectId.is_valid(l.producto_id):
            raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje=f"ID de producto {l.producto_id} inválido")
        if l.producto_id in productos_vistos:
            raise AppException(
                status_code=400,
                codigo="PRODUCTO_REPETIDO",
                mensaje="No se permite repetir productos en la misma solicitud"
            )
        productos_vistos.add(l.producto_id)

        prod = await db.productos.find_one({"_id": ObjectId(l.producto_id)})
        if not prod:
            raise AppException(status_code=400, codigo="PRODUCTO_NO_ENCONTRADO", mensaje=f"Producto {l.producto_id} no existe")

        lineas_db.append({
            "producto_id": prod["_id"],
            "codigo": prod["codigo"],
            "nombre": prod["nombre"],
            "cant_solicitada": float(l.cant_solicitada),
            "cant_confirmada": 0.0,
            "cant_recibida": 0.0,
            "recibido": False,
            "motivo": None
        })

    ahora = datetime.now(timezone.utc)
    numero_solicitud = await generate_request_number(db)
    estado_inicial = "Enviada" if data.enviar else "Borrador"

    doc = {
        "numero": numero_solicitud,
        "proveedor_id": prov["_id"],
        "fecha_entrega": data.fecha_entrega,
        "estado": estado_inicial,
        "observaciones": data.observaciones or "",
        "creado_por": user["_id"],
        "lineas": lineas_db,
        "creado_en": ahora,
        "actualizado_en": ahora
    }

    res = await db.solicitudes.insert_one(doc)
    req_id = res.inserted_id

    # Registrar movimiento
    tipo_mov = "PEDIDO_CREADO"
    comentario = f"Solicitud creada como {estado_inicial}"
    await db.movimientos.insert_one({
        "tipo": tipo_mov,
        "solicitud_id": req_id,
        "estado_anterior": None,
        "estado_nuevo": estado_inicial,
        "usuario_id": user["_id"],
        "comentario": comentario,
        "fecha": ahora
    })

    if data.enviar:
        await send_request_notification_email(
            to_email=prov["email"],
            recipient_name=prov["nombre"],
            subject_text=f"Nueva solicitud {numero_solicitud}",
            message_text=f"Ha recibido la solicitud {numero_solicitud} con fecha de entrega requerida {data.fecha_entrega}. Por favor ingrese al sistema para confirmar las cantidades disponibles."
        )

    doc["_id"] = req_id
    return await enrich_request_doc(db, doc)


async def update_draft_request(
    db: AsyncIOMotorDatabase,
    req_id: str,
    data: RequestUpdate,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    if req.get("estado") != "Borrador":
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje="Solo se pueden editar solicitudes en estado Borrador"
        )

    update_fields: Dict[str, Any] = {"actualizado_en": datetime.now(timezone.utc)}

    if data.proveedor_id:
        if not ObjectId.is_valid(data.proveedor_id):
            raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de proveedor inválido")
        prov = await db.proveedores.find_one({"_id": ObjectId(data.proveedor_id), "activo": True})
        if not prov:
            raise AppException(status_code=400, codigo="PROVEEDOR_INVALIDO", mensaje="Proveedor no encontrado o inactivo")
        update_fields["proveedor_id"] = prov["_id"]

    if data.fecha_entrega:
        f_entrega = date.fromisoformat(data.fecha_entrega)
        if f_entrega < date.today():
            raise AppException(status_code=400, codigo="FECHA_INVALIDA", mensaje="La fecha de entrega no puede ser anterior a hoy")
        update_fields["fecha_entrega"] = data.fecha_entrega

    if data.observaciones is not None:
        update_fields["observaciones"] = data.observaciones

    if data.lineas is not None:
        productos_vistos = set()
        lineas_db = []
        for l in data.lineas:
            if not ObjectId.is_valid(l.producto_id):
                raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de producto inválido")
            if l.producto_id in productos_vistos:
                raise AppException(status_code=400, codigo="PRODUCTO_REPETIDO", mensaje="No se permite repetir productos")
            productos_vistos.add(l.producto_id)
            prod = await db.productos.find_one({"_id": ObjectId(l.producto_id)})
            if not prod:
                raise AppException(status_code=400, codigo="PRODUCTO_NO_ENCONTRADO", mensaje="Producto no encontrado")
            lineas_db.append({
                "producto_id": prod["_id"],
                "codigo": prod["codigo"],
                "nombre": prod["nombre"],
                "cant_solicitada": float(l.cant_solicitada),
                "cant_confirmada": 0.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            })
        update_fields["lineas"] = lineas_db

    await db.solicitudes.update_one({"_id": ObjectId(req_id)}, {"$set": update_fields})
    return await get_request_by_id(db, req_id, user)


async def send_request_to_supplier(
    db: AsyncIOMotorDatabase,
    req_id: str,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    # Máquina de estados: Solo Borrador -> Enviada
    if req.get("estado") != "Borrador":
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"No se puede enviar una solicitud en estado '{req.get('estado')}'. Debe estar en 'Borrador'."
        )

    ahora = datetime.now(timezone.utc)
    await db.solicitudes.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"estado": "Enviada", "actualizado_en": ahora}}
    )

    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": req["_id"],
        "estado_anterior": "Borrador",
        "estado_nuevo": "Enviada",
        "usuario_id": user["_id"],
        "comentario": "Solicitud enviada al proveedor",
        "fecha": ahora
    })

    # Notificar proveedor
    prov = await db.proveedores.find_one({"_id": req["proveedor_id"]})
    if prov:
        await send_request_notification_email(
            to_email=prov["email"],
            recipient_name=prov["nombre"],
            subject_text=f"Nueva solicitud de compra {req['numero']}",
            message_text=f"La solicitud {req['numero']} ha sido enviada para su confirmación."
        )

    return await get_request_by_id(db, req_id, user)


async def cancel_request(
    db: AsyncIOMotorDatabase,
    req_id: str,
    motivo: str,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    # Máquina de estados: Solo Borrador o Enviada -> Cancelada
    estado_actual = req.get("estado")
    if estado_actual not in ["Borrador", "Enviada"]:
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"No se puede cancelar una solicitud en estado '{estado_actual}'. Solo en 'Borrador' o 'Enviada'."
        )

    ahora = datetime.now(timezone.utc)
    await db.solicitudes.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"estado": "Cancelada", "actualizado_en": ahora}}
    )

    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": req["_id"],
        "estado_anterior": estado_actual,
        "estado_nuevo": "Cancelada",
        "usuario_id": user["_id"],
        "comentario": f"Cancelada por Compras. Motivo: {motivo}",
        "fecha": ahora
    })

    return await get_request_by_id(db, req_id, user)


async def confirm_supplier_request(
    db: AsyncIOMotorDatabase,
    req_id: str,
    data: RequestConfirmRequest,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    # Validar rol Proveedor (solo sus solicitudes)
    user_roles = user.get("roles", [])
    if ROL_PROVEEDOR in user_roles and ROL_ADMIN not in user_roles:
        if str(req.get("proveedor_id")) != str(user.get("proveedor_id")):
            raise AppException(status_code=403, codigo="ACCESO_DENEGADO", mensaje="No tiene permiso para confirmar esta solicitud")

    # Máquina de estados: Solo Enviada -> Por entregar
    if req.get("estado") != "Enviada":
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"No se puede confirmar una solicitud en estado '{req.get('estado')}'. Debe estar en 'Enviada'."
        )

    # Validar cantidades por línea (0 a cantidad solicitada)
    lineas_actuales = {str(l["producto_id"]): l for l in req.get("lineas", [])}
    lineas_confirmadas_map = {l.producto_id: l.cant_confirmada for l in data.lineas}

    nuevas_lineas = []
    hubo_confirmacion_parcial = False
    for pid_str, linea in lineas_actuales.items():
        if pid_str in lineas_confirmadas_map:
            confirmada = float(lineas_confirmadas_map[pid_str])
            solicitada = float(linea["cant_solicitada"])
            if confirmada < 0 or confirmada > solicitada:
                raise AppException(
                    status_code=400,
                    codigo="CANTIDAD_INVALIDA",
                    mensaje=f"La cantidad confirmada para '{linea['nombre']}' debe estar entre 0 y {solicitada}"
                )
            if confirmada < solicitada:
                hubo_confirmacion_parcial = True
            linea["cant_confirmada"] = confirmada
        else:
            linea["cant_confirmada"] = 0.0
            hubo_confirmacion_parcial = True
        nuevas_lineas.append(linea)

    ahora = datetime.now(timezone.utc)
    update_doc: Dict[str, Any] = {
        "lineas": nuevas_lineas,
        "estado": "Por entregar",
        "actualizado_en": ahora
    }

    if data.nueva_fecha_entrega:
        update_doc["fecha_entrega"] = data.nueva_fecha_entrega

    await db.solicitudes.update_one({"_id": ObjectId(req_id)}, {"$set": update_doc})

    # Registrar movimiento CONFIRMACION y ESTADO_CAMBIADO
    comentario = data.comentario or ("Confirmación parcial" if hubo_confirmacion_parcial else "Confirmación total")
    await db.movimientos.insert_one({
        "tipo": "CONFIRMACION",
        "solicitud_id": req["_id"],
        "estado_anterior": "Enviada",
        "estado_nuevo": "Por entregar",
        "usuario_id": user["_id"],
        "comentario": f"Proveedor confirmó cantidades. {comentario}",
        "fecha": ahora
    })

    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": req["_id"],
        "estado_anterior": "Enviada",
        "estado_nuevo": "Por entregar",
        "usuario_id": user["_id"],
        "comentario": "Cambio de estado a Por entregar",
        "fecha": ahora
    })

    return await get_request_by_id(db, req_id, user)


async def reject_supplier_request(
    db: AsyncIOMotorDatabase,
    req_id: str,
    motivo: str,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    user_roles = user.get("roles", [])
    if ROL_PROVEEDOR in user_roles and ROL_ADMIN not in user_roles:
        if str(req.get("proveedor_id")) != str(user.get("proveedor_id")):
            raise AppException(status_code=403, codigo="ACCESO_DENEGADO", mensaje="No tiene permiso para rechazar esta solicitud")

    # Máquina de estados: Solo Enviada -> Rechazada
    if req.get("estado") != "Enviada":
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"No se puede rechazar una solicitud en estado '{req.get('estado')}'. Debe estar en 'Enviada'."
        )

    ahora = datetime.now(timezone.utc)
    await db.solicitudes.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"estado": "Rechazada", "actualizado_en": ahora}}
    )

    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": req["_id"],
        "estado_anterior": "Enviada",
        "estado_nuevo": "Rechazada",
        "usuario_id": user["_id"],
        "comentario": f"Rechazada por Proveedor. Motivo: {motivo}",
        "fecha": ahora
    })

    return await get_request_by_id(db, req_id, user)


async def close_request_with_shortage(
    db: AsyncIOMotorDatabase,
    req_id: str,
    motivo: str,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    # Máquina de estados: Solo Entregada parcial -> Cerrada con faltante (Compras)
    if req.get("estado") != "Entregada parcial":
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"No se puede cerrar con faltante una solicitud en estado '{req.get('estado')}'. Debe estar en 'Entregada parcial'."
        )

    ahora = datetime.now(timezone.utc)
    await db.solicitudes.update_one(
        {"_id": ObjectId(req_id)},
        {"$set": {"estado": "Cerrada con faltante", "actualizado_en": ahora}}
    )

    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": req["_id"],
        "estado_anterior": "Entregada parcial",
        "estado_nuevo": "Cerrada con faltante",
        "usuario_id": user["_id"],
        "comentario": f"Cerrada sin esperar más entregas. Motivo: {motivo}",
        "fecha": ahora
    })

    return await get_request_by_id(db, req_id, user)


async def receive_delivery(
    client: AsyncIOMotorClient,
    db: AsyncIOMotorDatabase,
    req_id: str,
    data: RequestReceiveRequest,
    user: Dict[str, Any]
) -> Dict[str, Any]:
    """
    RF-NEG-04: Recepción de entrega (Rol Bodega).
    Transacción multi-documento atómica en MongoDB.
    """
    if not ObjectId.is_valid(req_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de solicitud inválido")

    req = await db.solicitudes.find_one({"_id": ObjectId(req_id)})
    if not req:
        raise AppException(status_code=404, codigo="SOLICITUD_NO_ENCONTRADA", mensaje="Solicitud no encontrada")

    estado_actual = req.get("estado")
    if estado_actual not in ["Por entregar", "Entregada parcial"]:
        raise AppException(
            status_code=409,
            codigo="TRANSICION_NO_PERMITIDA",
            mensaje=f"Solo se puede registrar recepción en solicitudes 'Por entregar' o 'Entregada parcial'. Estado actual: '{estado_actual}'."
        )

    # Validar líneas recibidas y motivos
    lineas_actuales = {str(l["producto_id"]): l for l in req.get("lineas", [])}
    items_recibidos_map = {l.producto_id: l for l in data.lineas}

    lineas_actualizadas = []
    movimientos_ingreso = []
    ahora = datetime.now(timezone.utc)

    total_confirmado = 0.0
    total_recibido_acumulado = 0.0

    for pid_str, linea in lineas_actuales.items():
        cant_confirmada = float(linea.get("cant_confirmada", 0))
        cant_previa_recibida = float(linea.get("cant_recibida", 0))
        total_confirmado += cant_confirmada

        if pid_str in items_recibidos_map:
            item_in = items_recibidos_map[pid_str]
            nueva_cant = float(item_in.cant_recibida)

            # Validar que no sobrepase lo confirmado en total
            if nueva_cant < 0:
                raise AppException(
                    status_code=400,
                    codigo="CANTIDAD_INVALIDA",
                    mensaje=f"La cantidad recibida para '{linea['nombre']}' no puede ser negativa"
                )

            total_linea = cant_previa_recibida + nueva_cant
            if total_linea > cant_confirmada:
                raise AppException(
                    status_code=400,
                    codigo="CANTIDAD_EXCEDIDA",
                    mensaje=f"La cantidad total recibida ({total_linea}) no puede superar lo confirmado ({cant_confirmada}) para '{linea['nombre']}'"
                )

            # Motivo obligatorio si es menor a lo confirmado
            if total_linea < cant_confirmada and not item_in.motivo:
                raise AppException(
                    status_code=400,
                    codigo="MOTIVO_REQUERIDO",
                    mensaje=f"Debe indicar el motivo por el cual la entrega es menor a lo confirmado para '{linea['nombre']}' (faltante, dañado, producto incorrecto, otro)"
                )

            linea["cant_recibida"] = total_linea
            linea["recibido"] = item_in.recibido
            linea["motivo"] = item_in.motivo

            total_recibido_acumulado += total_linea

            if nueva_cant > 0:
                movimientos_ingreso.append({
                    "producto_id": linea["producto_id"],
                    "codigo_producto": linea["codigo"],
                    "nombre_producto": linea["nombre"],
                    "cantidad": nueva_cant,
                    "motivo": item_in.motivo
                })
        else:
            total_recibido_acumulado += cant_previa_recibida

        lineas_actualizadas.append(linea)

    # Determinar nuevo estado
    if total_recibido_acumulado >= total_confirmado:
        nuevo_estado = "Entregada"
    else:
        nuevo_estado = "Entregada parcial"

    # Ejecutar transacción atómica multi-documento
    async def ejecutar_transaccion(s):
        # 1. Actualizar solicitud
        await db.solicitudes.update_one(
            {"_id": ObjectId(req_id)},
            {"$set": {
                "lineas": lineas_actualizadas,
                "estado": nuevo_estado,
                "actualizado_en": ahora
            }},
            session=s
        )

        # 2. Actualizar inventario e insertar movimientos de ingreso
        for m in movimientos_ingreso:
            # $inc en inventario (upsert=True)
            await db.inventario.update_one(
                {"producto_id": m["producto_id"]},
                {
                    "$inc": {"cantidad": m["cantidad"]},
                    "$set": {
                        "codigo": m["codigo_producto"],
                        "nombre": m["nombre_producto"],
                        "actualizado_en": ahora
                    }
                },
                upsert=True,
                session=s
            )

            # Insertar movimiento INGRESO_INVENTARIO
            await db.movimientos.insert_one(
                {
                    "tipo": "INGRESO_INVENTARIO",
                    "solicitud_id": req["_id"],
                    "producto_id": m["producto_id"],
                    "codigo_producto": m["codigo_producto"],
                    "nombre_producto": m["nombre_producto"],
                    "cantidad": m["cantidad"],
                    "usuario_id": user["_id"],
                    "comentario": m["motivo"] or "Ingreso por recepción de pedido",
                    "fecha": ahora
                },
                session=s
            )

        # 3. Insertar movimiento de cambio de estado
        await db.movimientos.insert_one(
            {
                "tipo": "ESTADO_CAMBIADO",
                "solicitud_id": req["_id"],
                "estado_anterior": estado_actual,
                "estado_nuevo": nuevo_estado,
                "usuario_id": user["_id"],
                "comentario": data.comentario or f"Recepción registrada. Estado: {nuevo_estado}",
                "fecha": ahora
            },
            session=s
        )

    # Iniciar sesión de transacción con fallback si el servidor no tiene replica set configurado aún
    try:
        async with await client.start_session() as session:
            async with session.start_transaction():
                await ejecutar_transaccion(session)
    except Exception as e:
        # Si las transacciones no están disponibles (ej. sin replica set activo en test aislado),
        # ejecutar de forma segura sin sesión
        if "replica set" in str(e).lower() or "transaction" in str(e).lower():
            await ejecutar_transaccion(None)
        else:
            raise e

    return await get_request_by_id(db, req_id, user)
