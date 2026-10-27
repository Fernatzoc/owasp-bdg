from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import ROL_ADMIN, ROL_PROVEEDOR
from app.services.request_service import enrich_request_doc


async def query_movements(
    db: AsyncIOMotorDatabase,
    tipo: str,  # "pedidos", "ingresos", "cambios"
    user: Dict[str, Any],
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    proveedor_id: Optional[str] = None,
    producto_id: Optional[str] = None,
    numero_solicitud: Optional[str] = None,
    page: int = 1,
    size: int = 50
) -> Dict[str, Any]:
    user_roles = user.get("roles", [])
    es_proveedor = (ROL_PROVEEDOR in user_roles) and (ROL_ADMIN not in user_roles)
    prov_id_scoped = user.get("proveedor_id") if es_proveedor else proveedor_id

    # Pestaña 1: PEDIDOS
    if tipo == "pedidos":
        filtro: Dict[str, Any] = {}
        if es_proveedor:
            if not prov_id_scoped:
                return {"items": [], "total": 0, "page": page, "size": size, "pages": 1}
            filtro["proveedor_id"] = ObjectId(prov_id_scoped)
            filtro["estado"] = {"$ne": "Borrador"}
        elif prov_id_scoped and ObjectId.is_valid(prov_id_scoped):
            filtro["proveedor_id"] = ObjectId(prov_id_scoped)

        if numero_solicitud:
            filtro["numero"] = {"$regex": numero_solicitud, "$options": "i"}

        if producto_id and ObjectId.is_valid(producto_id):
            filtro["lineas.producto_id"] = ObjectId(producto_id)

        if fecha_desde or fecha_hasta:
            f_filtro = {}
            if fecha_desde:
                f_filtro["$gte"] = fecha_desde
            if fecha_hasta:
                f_filtro["$lte"] = fecha_hasta
            filtro["fecha_entrega"] = f_filtro

        skip = (page - 1) * size
        total = await db.solicitudes.count_documents(filtro)
        cursor = db.solicitudes.find(filtro).sort("creado_en", -1).skip(skip).limit(size)
        docs = await cursor.to_list(length=size)

        items = []
        for d in docs:
            enriched = await enrich_request_doc(db, d)
            items.append({
                "solicitud_id": enriched["id"],
                "numero": enriched["numero"],
                "proveedor": enriched["nombre_proveedor"],
                "fecha_creacion": enriched["creado_en"],
                "fecha_entrega": enriched["fecha_entrega"],
                "estado": enriched["estado"],
                "total_lineas": enriched["total_lineas"],
                "lineas": enriched["lineas"]
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 1
        }

    # Pestaña 2: PRODUCTOS INGRESADOS (tipo == "ingresos")
    elif tipo == "ingresos":
        filtro = {"tipo": "INGRESO_INVENTARIO"}

        # Si hay filtros de solicitud o proveedor, obtener los ids de solicitud correspondientes
        solicitud_filtro: Dict[str, Any] = {}
        if es_proveedor:
            if not prov_id_scoped:
                return {"items": [], "total": 0, "page": page, "size": size, "pages": 1}
            solicitud_filtro["proveedor_id"] = ObjectId(prov_id_scoped)
        elif prov_id_scoped and ObjectId.is_valid(prov_id_scoped):
            solicitud_filtro["proveedor_id"] = ObjectId(prov_id_scoped)

        if numero_solicitud:
            solicitud_filtro["numero"] = {"$regex": numero_solicitud, "$options": "i"}

        if solicitud_filtro:
            solicitudes = await db.solicitudes.find(solicitud_filtro, {"_id": 1}).to_list(length=5000)
            req_ids = [s["_id"] for s in solicitudes]
            filtro["solicitud_id"] = {"$in": req_ids}

        if producto_id and ObjectId.is_valid(producto_id):
            filtro["producto_id"] = ObjectId(producto_id)

        if fecha_desde or fecha_hasta:
            filtro_fecha = {}
            if fecha_desde:
                filtro_fecha["$gte"] = datetime.fromisoformat(fecha_desde)
            if fecha_hasta:
                filtro_fecha["$lte"] = datetime.fromisoformat(fecha_hasta + "T23:59:59")
            filtro["fecha"] = filtro_fecha

        skip = (page - 1) * size
        total = await db.movimientos.count_documents(filtro)
        cursor = db.movimientos.find(filtro).sort("fecha", -1).skip(skip).limit(size)
        docs = await cursor.to_list(length=size)

        items = []
        for d in docs:
            # Obtener número de solicitud y usuario
            sol_doc = await db.solicitudes.find_one({"_id": d["solicitud_id"]}, {"numero": 1})
            usr_doc = await db.usuarios.find_one({"_id": d["usuario_id"]}, {"nombre": 1})
            items.append({
                "id": str(d["_id"]),
                "fecha_recepcion": d["fecha"],
                "solicitud_id": str(d["solicitud_id"]),
                "numero_solicitud": sol_doc.get("numero", "N/A") if sol_doc else "N/A",
                "producto_id": str(d.get("producto_id", "")),
                "codigo_producto": d.get("codigo_producto", ""),
                "nombre_producto": d.get("nombre_producto", ""),
                "cantidad_recibida": float(d.get("cantidad", 0)),
                "usuario_recibio": usr_doc.get("nombre", "Sistema") if usr_doc else "Sistema"
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 1
        }

    # Pestaña 3: CAMBIOS DESDE PEDIDO HASTA ENTREGA (Línea de tiempo)
    elif tipo == "cambios":
        filtro = {}
        solicitud_filtro = {}
        if es_proveedor:
            if not prov_id_scoped:
                return {"items": [], "total": 0, "page": page, "size": size, "pages": 1}
            solicitud_filtro["proveedor_id"] = ObjectId(prov_id_scoped)
        elif prov_id_scoped and ObjectId.is_valid(prov_id_scoped):
            solicitud_filtro["proveedor_id"] = ObjectId(prov_id_scoped)

        if numero_solicitud:
            solicitud_filtro["numero"] = {"$regex": numero_solicitud, "$options": "i"}

        if solicitud_filtro:
            solicitudes = await db.solicitudes.find(solicitud_filtro, {"_id": 1}).to_list(length=5000)
            req_ids = [s["_id"] for s in solicitudes]
            filtro["solicitud_id"] = {"$in": req_ids}

        if fecha_desde or fecha_hasta:
            filtro_fecha = {}
            if fecha_desde:
                filtro_fecha["$gte"] = datetime.fromisoformat(fecha_desde)
            if fecha_hasta:
                filtro_fecha["$lte"] = datetime.fromisoformat(fecha_hasta + "T23:59:59")
            filtro["fecha"] = filtro_fecha

        skip = (page - 1) * size
        total = await db.movimientos.count_documents(filtro)
        cursor = db.movimientos.find(filtro).sort("fecha", -1).skip(skip).limit(size)
        docs = await cursor.to_list(length=size)

        items = []
        for d in docs:
            sol_doc = await db.solicitudes.find_one({"_id": d["solicitud_id"]}, {"numero": 1})
            usr_doc = await db.usuarios.find_one({"_id": d["usuario_id"]}, {"nombre": 1})
            items.append({
                "id": str(d["_id"]),
                "solicitud_id": str(d["solicitud_id"]),
                "numero_solicitud": sol_doc.get("numero", "N/A") if sol_doc else "N/A",
                "tipo_movimiento": d.get("tipo"),
                "estado_anterior": d.get("estado_anterior"),
                "estado_nuevo": d.get("estado_nuevo"),
                "cantidad": d.get("cantidad"),
                "codigo_producto": d.get("codigo_producto"),
                "nombre_producto": d.get("nombre_producto"),
                "usuario": usr_doc.get("nombre", "Sistema") if usr_doc else "Sistema",
                "comentario": d.get("comentario", ""),
                "fecha_hora": d["fecha"]
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 1
        }

    else:
        return {"items": [], "total": 0, "page": page, "size": size, "pages": 1}
