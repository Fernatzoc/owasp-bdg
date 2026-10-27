import csv
import io
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


async def list_inventory(
    db: AsyncIOMotorDatabase,
    query: Optional[str] = None,
    sort_by: str = "codigo",
    sort_order: int = 1,  # 1 asc, -1 desc
    page: int = 1,
    size: int = 50
) -> Dict[str, Any]:
    filtro: Dict[str, Any] = {}
    if query:
        filtro["$or"] = [
            {"codigo": {"$regex": query, "$options": "i"}},
            {"nombre": {"$regex": query, "$options": "i"}}
        ]

    valid_sorts = ["codigo", "nombre", "cantidad", "actualizado_en"]
    sort_field = sort_by if sort_by in valid_sorts else "codigo"

    skip = (page - 1) * size
    total = await db.inventario.count_documents(filtro)
    cursor = db.inventario.find(filtro).sort(sort_field, sort_order).skip(skip).limit(size)
    docs = await cursor.to_list(length=size)

    items = []
    for d in docs:
        items.append({
            "id": str(d["_id"]),
            "producto_id": str(d.get("producto_id", "")),
            "codigo": d.get("codigo", ""),
            "nombre": d.get("nombre", ""),
            "cantidad": float(d.get("cantidad", 0)),
            "actualizado_en": d.get("actualizado_en")
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size if total > 0 else 1
    }


async def export_inventory_csv(db: AsyncIOMotorDatabase) -> str:
    cursor = db.inventario.find({}).sort("codigo", 1)
    docs = await cursor.to_list(length=10000)

    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Código", "Nombre del Producto", "Cantidad Disponible", "Última Actualización"])

    for d in docs:
        actualizado = d.get("actualizado_en").strftime("%d/%m/%Y %H:%M:%S") if d.get("actualizado_en") else ""
        writer.writerow([
            d.get("codigo", ""),
            d.get("nombre", ""),
            f"{d.get('cantidad', 0):.2f}",
            actualizado
        ])

    return output.getvalue()
