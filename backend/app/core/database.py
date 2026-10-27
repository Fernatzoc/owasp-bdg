import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING, TEXT
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db_manager = DatabaseManager()


async def get_database() -> AsyncIOMotorDatabase:
    if db_manager.db is None:
        raise RuntimeError("Base de datos no inicializada")
    return db_manager.db


async def get_client() -> AsyncIOMotorClient:
    if db_manager.client is None:
        raise RuntimeError("Cliente MongoDB no inicializado")
    return db_manager.client


async def init_db():
    """Conecta a MongoDB y crea las colecciones e índices necesarios."""
    logger.info("Conectando a MongoDB: %s", settings.MONGODB_URL)
    db_manager.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_manager.db = db_manager.client[settings.DATABASE_NAME]

    db = db_manager.db

    # 1. usuarios
    await db.usuarios.create_indexes([
        IndexModel([("email", ASCENDING)], unique=True, name="idx_usuarios_email_unique")
    ])

    # 2. roles
    await db.roles.create_indexes([
        IndexModel([("nombre", ASCENDING)], unique=True, name="idx_roles_nombre_unique")
    ])

    # 3. sesiones
    # Índices únicos parciales para garantizar una sesión activa por usuario y por dispositivo
    await db.sesiones.create_indexes([
        IndexModel(
            [("usuario_id", ASCENDING), ("activa", ASCENDING)],
            unique=True,
            partialFilterExpression={"activa": True},
            name="idx_sesiones_usuario_activa_unique"
        ),
        IndexModel(
            [("dispositivo_id", ASCENDING), ("activa", ASCENDING)],
            unique=True,
            partialFilterExpression={"activa": True},
            name="idx_sesiones_dispositivo_activa_unique"
        ),
        IndexModel(
            [("expira_en", ASCENDING)],
            expireAfterSeconds=0,
            name="idx_sesiones_ttl"
        )
    ])

    # 4. tokens_verificacion
    await db.tokens_verificacion.create_indexes([
        IndexModel(
            [("expira_en", ASCENDING)],
            expireAfterSeconds=0,
            name="idx_tokens_ttl"
        ),
        IndexModel([("codigo_hash", ASCENDING)], name="idx_tokens_codigo_hash"),
        IndexModel([("usuario_id", ASCENDING), ("tipo", ASCENDING)], name="idx_tokens_usuario_tipo")
    ])

    # 5. productos
    await db.productos.create_indexes([
        IndexModel([("codigo", ASCENDING)], unique=True, name="idx_productos_codigo_unique"),
        IndexModel([("nombre", TEXT)], name="idx_productos_nombre_text")
    ])

    # 6. proveedores
    await db.proveedores.create_indexes([
        IndexModel([("codigo", ASCENDING)], unique=True, name="idx_proveedores_codigo_unique")
    ])

    # 7. solicitudes
    await db.solicitudes.create_indexes([
        IndexModel([("numero", ASCENDING)], unique=True, name="idx_solicitudes_numero_unique"),
        IndexModel([("proveedor_id", ASCENDING), ("estado", ASCENDING)], name="idx_solicitudes_prov_estado"),
        IndexModel([("fecha_entrega", ASCENDING)], name="idx_solicitudes_fecha_entrega")
    ])

    # 8. inventario
    await db.inventario.create_indexes([
        IndexModel([("producto_id", ASCENDING)], unique=True, name="idx_inventario_producto_unique")
    ])

    # 9. movimientos
    await db.movimientos.create_indexes([
        IndexModel([("solicitud_id", ASCENDING), ("fecha", ASCENDING)], name="idx_movimientos_solicitud_fecha"),
        IndexModel([("tipo", ASCENDING), ("fecha", ASCENDING)], name="idx_movimientos_tipo_fecha")
    ])

    # 10. bitacora_seguridad
    await db.bitacora_seguridad.create_indexes([
        IndexModel([("fecha", ASCENDING)], name="idx_bitacora_fecha"),
        IndexModel([("usuario_id", ASCENDING)], name="idx_bitacora_usuario")
    ])

    logger.info("Índices y colecciones de MongoDB inicializados correctamente")


async def close_db():
    """Cierra la conexión con MongoDB."""
    if db_manager.client:
        logger.info("Cerrando conexión a MongoDB...")
        db_manager.client.close()
