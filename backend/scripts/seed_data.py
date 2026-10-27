import asyncio
import logging
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient

import sys
import os
# Asegurar que el path incluya backend para importar app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings, PERMISOS_POR_ROL
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def seed():
    logger.info("Iniciando carga de datos de ejemplo (seed data)...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]

    ahora = datetime.now(timezone.utc)
    ayer = ahora - timedelta(days=1)
    hace_tres_dias = ahora - timedelta(days=3)
    fecha_futura_1 = (ahora + timedelta(days=5)).strftime("%Y-%m-%d")
    fecha_futura_2 = (ahora + timedelta(days=8)).strftime("%Y-%m-%d")

    # 1. Limpiar colecciones previas
    logger.info("Limpiando colecciones existentes...")
    collections = [
        "usuarios", "roles", "sesiones", "tokens_verificacion",
        "productos", "proveedores", "solicitudes", "inventario",
        "movimientos", "bitacora_seguridad"
    ]
    for col in collections:
        await db[col].delete_many({})

    # 2. Roles
    logger.info("Creando roles del sistema...")
    roles_docs = [
        {"nombre": rol, "descripcion": f"Rol {rol}", "permisos": permisos}
        for rol, permisos in PERMISOS_POR_ROL.items()
    ]
    await db.roles.insert_many(roles_docs)

    # 3. Proveedores (3)
    logger.info("Insertando 3 proveedores...")
    proveedores_data = [
        {
            "codigo": "PROV-001",
            "nombre": "Distribuidora Industrial de Guatemala, S.A.",
            "nit": "8765432-1",
            "email": "proveedor@empresa.com",
            "telefono": "+502 2345-6789",
            "activo": True
        },
        {
            "codigo": "PROV-002",
            "nombre": "Suministros Globales del Pacífico, S.A.",
            "nit": "1234567-8",
            "email": "contacto@suministrosglobales.com",
            "telefono": "+502 2456-7890",
            "activo": True
        },
        {
            "codigo": "PROV-003",
            "nombre": "Soluciones Logísticas y Empaques S.A.",
            "nit": "9876543-2",
            "email": "ventas@solucioneslogisticas.gt",
            "telefono": "+502 2567-8901",
            "activo": True
        }
    ]
    res_prov = await db.proveedores.insert_many(proveedores_data)
    prov_ids = res_prov.inserted_ids
    prov1_id = prov_ids[0]
    prov2_id = prov_ids[1]
    prov3_id = prov_ids[2]

    # 4. Usuarios (1 por rol) - Contraseña común: Password2026!
    logger.info("Creando usuarios por cada rol...")
    password_comun = "Password2026!"
    pw_hash = get_password_hash(password_comun)

    usuarios_data = [
        {
            "nombre": "Administrador Principal",
            "email": "admin@empresa.com",
            "password_hash": pw_hash,
            "roles": ["Administrador"],
            "proveedor_id": None,
            "estado": "activo",
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
            "historial_passwords": [pw_hash],
            "creado_en": hace_tres_dias
        },
        {
            "nombre": "Carlos Gómez - Compras",
            "email": "compras@empresa.com",
            "password_hash": pw_hash,
            "roles": ["Compras"],
            "proveedor_id": None,
            "estado": "activo",
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
            "historial_passwords": [pw_hash],
            "creado_en": hace_tres_dias
        },
        {
            "nombre": "Representante Proveedor Industrial",
            "email": "proveedor@empresa.com",
            "password_hash": pw_hash,
            "roles": ["Proveedor"],
            "proveedor_id": prov1_id,
            "estado": "activo",
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
            "historial_passwords": [pw_hash],
            "creado_en": hace_tres_dias
        },
        {
            "nombre": "Marta Reyes - Bodega",
            "email": "bodega@empresa.com",
            "password_hash": pw_hash,
            "roles": ["Bodega"],
            "proveedor_id": None,
            "estado": "activo",
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
            "historial_passwords": [pw_hash],
            "creado_en": hace_tres_dias
        },
        {
            "nombre": "Juan Consulta - Auditoría",
            "email": "consulta@empresa.com",
            "password_hash": pw_hash,
            "roles": ["Consulta"],
            "proveedor_id": None,
            "estado": "activo",
            "intentos_fallidos": 0,
            "bloqueado_hasta": None,
            "historial_passwords": [pw_hash],
            "creado_en": hace_tres_dias
        }
    ]
    res_usr = await db.usuarios.insert_many(usuarios_data)
    usr_ids = res_usr.inserted_ids
    admin_id = usr_ids[0]
    compras_id = usr_ids[1]
    proveedor_user_id = usr_ids[2]
    bodega_id = usr_ids[3]

    # 5. Productos (10)
    logger.info("Insertando 10 productos...")
    productos_data = [
        {"codigo": "PROD-001", "nombre": "Caja de Cartón Corrugado 40x30x30", "descripcion": "Caja resistente para embalaje pesado", "unidad": "unidad", "activo": True},
        {"codigo": "PROD-002", "nombre": "Cinta Adhesiva Industrial 2 pulg x 100m", "descripcion": "Cinta transparente de alta adherencia", "unidad": "rollo", "activo": True},
        {"codigo": "PROD-003", "nombre": "Película Stretch Film 18 pulg Calibre 70", "descripcion": "Rollo de plástico para emplayar tarimas", "unidad": "rollo", "activo": True},
        {"codigo": "PROD-004", "nombre": "Pallet de Madera Estándar 1.20x1.00m", "descripcion": "Tarima de cuatro entradas tratada térmicamente", "unidad": "unidad", "activo": True},
        {"codigo": "PROD-005", "nombre": "Esquineros Protectores de Cartón 1.5m", "descripcion": "Protección de esquinas para estiba", "unidad": "unidad", "activo": True},
        {"codigo": "PROD-006", "nombre": "Fleje Plástico de Polipropileno 1/2 pulg", "descripcion": "Bobina de fleje negro de 2000m", "unidad": "rollo", "activo": True},
        {"codigo": "PROD-007", "nombre": "Grapas Metálicas para Fleje 1/2 pulg", "descripcion": "Caja con 1000 sellos de lámina galvanizada", "unidad": "caja", "activo": True},
        {"codigo": "PROD-008", "nombre": "Bolsa de Poliburbuja Antiestática 20x25", "descripcion": "Paquete con 100 bolsas de protección", "unidad": "paquete", "activo": True},
        {"codigo": "PROD-009", "nombre": "Etiquetas Térmicas 4x6 pulgadas", "descripcion": "Rollo de 500 etiquetas autoadhesivas", "unidad": "rollo", "activo": True},
        {"codigo": "PROD-010", "nombre": "Marcador Permanente Industrial Negro", "descripcion": "Punta gruesa indeleble para cajas", "unidad": "unidad", "activo": True}
    ]
    res_prod = await db.productos.insert_many(productos_data)
    prod_ids = res_prod.inserted_ids

    # 6. Inventario inicial
    logger.info("Inicializando inventario...")
    cantidades_iniciales = [150, 80, 45, 20, 200, 15, 50, 100, 60, 30]
    inventario_data = [
        {
            "producto_id": prod_ids[i],
            "codigo": productos_data[i]["codigo"],
            "nombre": productos_data[i]["nombre"],
            "cantidad": float(cantidades_iniciales[i]),
            "actualizado_en": hace_tres_dias
        }
        for i in range(10)
    ]
    await db.inventario.insert_many(inventario_data)

    # 7. Solicitudes (5 en estados distintos)
    logger.info("Creando 5 solicitudes en estados distintos...")

    # S1: Borrador (SOL-2026-000001)
    s1 = {
        "numero": "SOL-2026-000001",
        "proveedor_id": prov2_id,
        "fecha_entrega": fecha_futura_1,
        "estado": "Borrador",
        "observaciones": "Borrador en preparación para suministros de empaque",
        "creado_por": compras_id,
        "lineas": [
            {
                "producto_id": prod_ids[0],
                "codigo": productos_data[0]["codigo"],
                "nombre": productos_data[0]["nombre"],
                "cant_solicitada": 50.0,
                "cant_confirmada": 0.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            },
            {
                "producto_id": prod_ids[1],
                "codigo": productos_data[1]["codigo"],
                "nombre": productos_data[1]["nombre"],
                "cant_solicitada": 20.0,
                "cant_confirmada": 0.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            }
        ],
        "creado_en": ayer,
        "actualizado_en": ayer
    }
    res_s1 = await db.solicitudes.insert_one(s1)
    await db.movimientos.insert_one({
        "tipo": "PEDIDO_CREADO",
        "solicitud_id": res_s1.inserted_id,
        "estado_anterior": None,
        "estado_nuevo": "Borrador",
        "usuario_id": compras_id,
        "comentario": "Solicitud creada en borrador",
        "fecha": ayer
    })

    # S2: Enviada (SOL-2026-000002) - Proveedor 1
    s2 = {
        "numero": "SOL-2026-000002",
        "proveedor_id": prov1_id,
        "fecha_entrega": fecha_futura_1,
        "estado": "Enviada",
        "observaciones": "Urgente para producción de fin de mes",
        "creado_por": compras_id,
        "lineas": [
            {
                "producto_id": prod_ids[2],
                "codigo": productos_data[2]["codigo"],
                "nombre": productos_data[2]["nombre"],
                "cant_solicitada": 30.0,
                "cant_confirmada": 0.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            },
            {
                "producto_id": prod_ids[3],
                "codigo": productos_data[3]["codigo"],
                "nombre": productos_data[3]["nombre"],
                "cant_solicitada": 15.0,
                "cant_confirmada": 0.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            }
        ],
        "creado_en": ayer,
        "actualizado_en": ayer
    }
    res_s2 = await db.solicitudes.insert_one(s2)
    await db.movimientos.insert_one({
        "tipo": "PEDIDO_CREADO",
        "solicitud_id": res_s2.inserted_id,
        "estado_anterior": None,
        "estado_nuevo": "Borrador",
        "usuario_id": compras_id,
        "comentario": "Solicitud creada",
        "fecha": ayer
    })
    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": res_s2.inserted_id,
        "estado_anterior": "Borrador",
        "estado_nuevo": "Enviada",
        "usuario_id": compras_id,
        "comentario": "Solicitud enviada al proveedor",
        "fecha": ayer
    })

    # S3: Por entregar (SOL-2026-000003) - Proveedor 1 (Confirmación total)
    s3 = {
        "numero": "SOL-2026-000003",
        "proveedor_id": prov1_id,
        "fecha_entrega": fecha_futura_2,
        "estado": "Por entregar",
        "observaciones": "Entrega confirmada para la próxima semana",
        "creado_por": compras_id,
        "lineas": [
            {
                "producto_id": prod_ids[4],
                "codigo": productos_data[4]["codigo"],
                "nombre": productos_data[4]["nombre"],
                "cant_solicitada": 100.0,
                "cant_confirmada": 100.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            },
            {
                "producto_id": prod_ids[5],
                "codigo": productos_data[5]["codigo"],
                "nombre": productos_data[5]["nombre"],
                "cant_solicitada": 10.0,
                "cant_confirmada": 10.0,
                "cant_recibida": 0.0,
                "recibido": False,
                "motivo": None
            }
        ],
        "creado_en": hace_tres_dias,
        "actualizado_en": ayer
    }
    res_s3 = await db.solicitudes.insert_one(s3)
    await db.movimientos.insert_one({
        "tipo": "PEDIDO_CREADO",
        "solicitud_id": res_s3.inserted_id,
        "estado_anterior": None,
        "estado_nuevo": "Borrador",
        "usuario_id": compras_id,
        "comentario": "Solicitud creada",
        "fecha": hace_tres_dias
    })
    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": res_s3.inserted_id,
        "estado_anterior": "Borrador",
        "estado_nuevo": "Enviada",
        "usuario_id": compras_id,
        "comentario": "Solicitud enviada al proveedor",
        "fecha": hace_tres_dias
    })
    await db.movimientos.insert_one({
        "tipo": "CONFIRMACION",
        "solicitud_id": res_s3.inserted_id,
        "estado_anterior": "Enviada",
        "estado_nuevo": "Por entregar",
        "usuario_id": proveedor_user_id,
        "comentario": "Proveedor confirmó entrega total",
        "fecha": ayer
    })

    # S4: Entregada parcial (SOL-2026-000004) - Proveedor 1
    s4 = {
        "numero": "SOL-2026-000004",
        "proveedor_id": prov1_id,
        "fecha_entrega": ayer.strftime("%Y-%m-%d"),
        "estado": "Entregada parcial",
        "observaciones": "Se recibió primer lote con faltante de 10 rollos",
        "creado_por": compras_id,
        "lineas": [
            {
                "producto_id": prod_ids[6],
                "codigo": productos_data[6]["codigo"],
                "nombre": productos_data[6]["nombre"],
                "cant_solicitada": 25.0,
                "cant_confirmada": 25.0,
                "cant_recibida": 25.0,
                "recibido": True,
                "motivo": None
            },
            {
                "producto_id": prod_ids[7],
                "codigo": productos_data[7]["codigo"],
                "nombre": productos_data[7]["nombre"],
                "cant_solicitada": 30.0,
                "cant_confirmada": 30.0,
                "cant_recibida": 20.0,
                "recibido": False,
                "motivo": "faltante"
            }
        ],
        "creado_en": hace_tres_dias,
        "actualizado_en": ahora
    }
    res_s4 = await db.solicitudes.insert_one(s4)
    await db.movimientos.insert_one({
        "tipo": "PEDIDO_CREADO",
        "solicitud_id": res_s4.inserted_id,
        "estado_anterior": None,
        "estado_nuevo": "Borrador",
        "usuario_id": compras_id,
        "comentario": "Solicitud creada",
        "fecha": hace_tres_dias
    })
    await db.movimientos.insert_one({
        "tipo": "CONFIRMACION",
        "solicitud_id": res_s4.inserted_id,
        "estado_anterior": "Enviada",
        "estado_nuevo": "Por entregar",
        "usuario_id": proveedor_user_id,
        "comentario": "Proveedor confirmó cantidades",
        "fecha": ayer
    })
    # Movimiento ingreso inventario
    await db.movimientos.insert_one({
        "tipo": "INGRESO_INVENTARIO",
        "solicitud_id": res_s4.inserted_id,
        "producto_id": prod_ids[6],
        "codigo_producto": productos_data[6]["codigo"],
        "nombre_producto": productos_data[6]["nombre"],
        "cantidad": 25.0,
        "usuario_id": bodega_id,
        "comentario": "Recepción completa de línea",
        "fecha": ahora
    })
    await db.movimientos.insert_one({
        "tipo": "INGRESO_INVENTARIO",
        "solicitud_id": res_s4.inserted_id,
        "producto_id": prod_ids[7],
        "codigo_producto": productos_data[7]["codigo"],
        "nombre_producto": productos_data[7]["nombre"],
        "cantidad": 20.0,
        "usuario_id": bodega_id,
        "comentario": "faltante",
        "fecha": ahora
    })
    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": res_s4.inserted_id,
        "estado_anterior": "Por entregar",
        "estado_nuevo": "Entregada parcial",
        "usuario_id": bodega_id,
        "comentario": "Recepción parcial registrada con faltantes",
        "fecha": ahora
    })

    # S5: Entregada (SOL-2026-000005) - Proveedor 3 (Completa)
    s5 = {
        "numero": "SOL-2026-000005",
        "proveedor_id": prov3_id,
        "fecha_entrega": ayer.strftime("%Y-%m-%d"),
        "estado": "Entregada",
        "observaciones": "Entrega recibida satisfactoriamente al 100%",
        "creado_por": compras_id,
        "lineas": [
            {
                "producto_id": prod_ids[8],
                "codigo": productos_data[8]["codigo"],
                "nombre": productos_data[8]["nombre"],
                "cant_solicitada": 40.0,
                "cant_confirmada": 40.0,
                "cant_recibida": 40.0,
                "recibido": True,
                "motivo": None
            },
            {
                "producto_id": prod_ids[9],
                "codigo": productos_data[9]["codigo"],
                "nombre": productos_data[9]["nombre"],
                "cant_solicitada": 15.0,
                "cant_confirmada": 15.0,
                "cant_recibida": 15.0,
                "recibido": True,
                "motivo": None
            }
        ],
        "creado_en": hace_tres_dias,
        "actualizado_en": ayer
    }
    res_s5 = await db.solicitudes.insert_one(s5)
    await db.movimientos.insert_one({
        "tipo": "PEDIDO_CREADO",
        "solicitud_id": res_s5.inserted_id,
        "estado_anterior": None,
        "estado_nuevo": "Borrador",
        "usuario_id": compras_id,
        "comentario": "Solicitud creada",
        "fecha": hace_tres_dias
    })
    await db.movimientos.insert_one({
        "tipo": "CONFIRMACION",
        "solicitud_id": res_s5.inserted_id,
        "estado_anterior": "Enviada",
        "estado_nuevo": "Por entregar",
        "usuario_id": admin_id,
        "comentario": "Proveedor confirmó cantidades",
        "fecha": hace_tres_dias
    })
    await db.movimientos.insert_one({
        "tipo": "INGRESO_INVENTARIO",
        "solicitud_id": res_s5.inserted_id,
        "producto_id": prod_ids[8],
        "codigo_producto": productos_data[8]["codigo"],
        "nombre_producto": productos_data[8]["nombre"],
        "cantidad": 40.0,
        "usuario_id": bodega_id,
        "comentario": "Recepción completa",
        "fecha": ayer
    })
    await db.movimientos.insert_one({
        "tipo": "INGRESO_INVENTARIO",
        "solicitud_id": res_s5.inserted_id,
        "producto_id": prod_ids[9],
        "codigo_producto": productos_data[9]["codigo"],
        "nombre_producto": productos_data[9]["nombre"],
        "cantidad": 15.0,
        "usuario_id": bodega_id,
        "comentario": "Recepción completa",
        "fecha": ayer
    })
    await db.movimientos.insert_one({
        "tipo": "ESTADO_CAMBIADO",
        "solicitud_id": res_s5.inserted_id,
        "estado_anterior": "Por entregar",
        "estado_nuevo": "Entregada",
        "usuario_id": bodega_id,
        "comentario": "Recepción finalizada con éxito",
        "fecha": ayer
    })

    # Bitácora inicial
    await db.bitacora_seguridad.insert_one({
        "evento": "SISTEMA_INICIALIZADO",
        "usuario_id": admin_id,
        "email": "admin@empresa.com",
        "ip": "127.0.0.1",
        "dispositivo_id": "seed-system",
        "exito": True,
        "detalle": "Seed data cargada con éxito: 10 productos, 3 proveedores, 5 usuarios y 5 solicitudes",
        "fecha": ahora
    })

    client.close()
    logger.info("✅ Carga de datos de ejemplo completada con éxito!")
    logger.info("Usuarios creados (Contraseña para todos: 'Password2026!'):")
    logger.info(" - Administrador: admin@empresa.com")
    logger.info(" - Compras:       compras@empresa.com")
    logger.info(" - Proveedor:     proveedor@empresa.com (vinculado a PROV-001)")
    logger.info(" - Bodega:        bodega@empresa.com")
    logger.info(" - Consulta:      consulta@empresa.com")


if __name__ == "__main__":
    asyncio.run(seed())
