from typing import Optional, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.exceptions import AppException
from app.schemas.product import ProductCreate, ProductUpdate
from app.schemas.supplier import SupplierCreate, SupplierUpdate


# ==================== PRODUCTOS ====================

async def list_products(
    db: AsyncIOMotorDatabase,
    query: Optional[str] = None,
    activo: Optional[bool] = None,
    page: int = 1,
    size: int = 50
) -> Dict[str, Any]:
    filtro: Dict[str, Any] = {}
    if query:
        filtro["$or"] = [
            {"codigo": {"$regex": query, "$options": "i"}},
            {"nombre": {"$regex": query, "$options": "i"}},
            {"descripcion": {"$regex": query, "$options": "i"}}
        ]
    if activo is not None:
        filtro["activo"] = activo

    skip = (page - 1) * size
    total = await db.productos.count_documents(filtro)
    cursor = db.productos.find(filtro).sort("codigo", 1).skip(skip).limit(size)
    productos = await cursor.to_list(length=size)

    items = []
    for p in productos:
        items.append({
            "id": str(p["_id"]),
            "codigo": p["codigo"],
            "nombre": p["nombre"],
            "descripcion": p.get("descripcion", ""),
            "unidad": p.get("unidad", "unidad"),
            "activo": p.get("activo", True)
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


async def get_product_by_id(db: AsyncIOMotorDatabase, product_id: str) -> Dict[str, Any]:
    if not ObjectId.is_valid(product_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de producto inválido")

    p = await db.productos.find_one({"_id": ObjectId(product_id)})
    if not p:
        raise AppException(status_code=404, codigo="PRODUCTO_NO_ENCONTRADO", mensaje="Producto no encontrado")

    return {
        "id": str(p["_id"]),
        "codigo": p["codigo"],
        "nombre": p["nombre"],
        "descripcion": p.get("descripcion", ""),
        "unidad": p.get("unidad", "unidad"),
        "activo": p.get("activo", True)
    }


async def create_product(db: AsyncIOMotorDatabase, data: ProductCreate) -> Dict[str, Any]:
    codigo = data.codigo.strip().upper()
    existente = await db.productos.find_one({"codigo": codigo})
    if existente:
        raise AppException(
            status_code=400,
            codigo="CODIGO_DUPLICADO",
            mensaje=f"Ya existe un producto con el código '{codigo}'"
        )

    doc = {
        "codigo": codigo,
        "nombre": data.nombre.strip(),
        "descripcion": data.descripcion.strip() if data.descripcion else "",
        "unidad": data.unidad.strip(),
        "activo": data.activo
    }
    res = await db.productos.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc


async def update_product(db: AsyncIOMotorDatabase, product_id: str, data: ProductUpdate) -> Dict[str, Any]:
    if not ObjectId.is_valid(product_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de producto inválido")

    update_doc: Dict[str, Any] = {}
    if data.nombre is not None:
        update_doc["nombre"] = data.nombre.strip()
    if data.descripcion is not None:
        update_doc["descripcion"] = data.descripcion.strip()
    if data.unidad is not None:
        update_doc["unidad"] = data.unidad.strip()
    if data.activo is not None:
        update_doc["activo"] = data.activo

    if not update_doc:
        return await get_product_by_id(db, product_id)

    res = await db.productos.update_one({"_id": ObjectId(product_id)}, {"$set": update_doc})
    if res.matched_count == 0:
        raise AppException(status_code=404, codigo="PRODUCTO_NO_ENCONTRADO", mensaje="Producto no encontrado")

    return await get_product_by_id(db, product_id)


# ==================== PROVEEDORES ====================

async def list_suppliers(
    db: AsyncIOMotorDatabase,
    query: Optional[str] = None,
    activo: Optional[bool] = None,
    page: int = 1,
    size: int = 50
) -> Dict[str, Any]:
    filtro: Dict[str, Any] = {}
    if query:
        filtro["$or"] = [
            {"codigo": {"$regex": query, "$options": "i"}},
            {"nombre": {"$regex": query, "$options": "i"}},
            {"nit": {"$regex": query, "$options": "i"}}
        ]
    if activo is not None:
        filtro["activo"] = activo

    skip = (page - 1) * size
    total = await db.proveedores.count_documents(filtro)
    cursor = db.proveedores.find(filtro).sort("codigo", 1).skip(skip).limit(size)
    proveedores = await cursor.to_list(length=size)

    items = []
    for p in proveedores:
        items.append({
            "id": str(p["_id"]),
            "codigo": p["codigo"],
            "nombre": p["nombre"],
            "nit": p["nit"],
            "email": p["email"],
            "telefono": p.get("telefono", ""),
            "activo": p.get("activo", True)
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


async def get_supplier_by_id(db: AsyncIOMotorDatabase, supplier_id: str) -> Dict[str, Any]:
    if not ObjectId.is_valid(supplier_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de proveedor inválido")

    p = await db.proveedores.find_one({"_id": ObjectId(supplier_id)})
    if not p:
        raise AppException(status_code=404, codigo="PROVEEDOR_NO_ENCONTRADO", mensaje="Proveedor no encontrado")

    return {
        "id": str(p["_id"]),
        "codigo": p["codigo"],
        "nombre": p["nombre"],
        "nit": p["nit"],
        "email": p["email"],
        "telefono": p.get("telefono", ""),
        "activo": p.get("activo", True)
    }


async def create_supplier(db: AsyncIOMotorDatabase, data: SupplierCreate) -> Dict[str, Any]:
    codigo = data.codigo.strip().upper()
    existente = await db.proveedores.find_one({"codigo": codigo})
    if existente:
        raise AppException(
            status_code=400,
            codigo="CODIGO_DUPLICADO",
            mensaje=f"Ya existe un proveedor con el código '{codigo}'"
        )

    doc = {
        "codigo": codigo,
        "nombre": data.nombre.strip(),
        "nit": data.nit.strip(),
        "email": data.email.lower().strip(),
        "telefono": data.telefono.strip() if data.telefono else "",
        "activo": data.activo
    }
    res = await db.proveedores.insert_one(doc)
    doc["id"] = str(res.inserted_id)
    return doc


async def update_supplier(db: AsyncIOMotorDatabase, supplier_id: str, data: SupplierUpdate) -> Dict[str, Any]:
    if not ObjectId.is_valid(supplier_id):
        raise AppException(status_code=400, codigo="ID_INVALIDO", mensaje="ID de proveedor inválido")

    update_doc: Dict[str, Any] = {}
    if data.nombre is not None:
        update_doc["nombre"] = data.nombre.strip()
    if data.nit is not None:
        update_doc["nit"] = data.nit.strip()
    if data.email is not None:
        update_doc["email"] = data.email.lower().strip()
    if data.telefono is not None:
        update_doc["telefono"] = data.telefono.strip()
    if data.activo is not None:
        update_doc["activo"] = data.activo

    if not update_doc:
        return await get_supplier_by_id(db, supplier_id)

    res = await db.proveedores.update_one({"_id": ObjectId(supplier_id)}, {"$set": update_doc})
    if res.matched_count == 0:
        raise AppException(status_code=404, codigo="PROVEEDOR_NO_ENCONTRADO", mensaje="Proveedor no encontrado")

    return await get_supplier_by_id(db, supplier_id)
