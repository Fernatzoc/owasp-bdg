from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Sistema de Solicitudes a Proveedores e Inventario"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "super_secreto_para_jwt_seguro_y_con_longitud_adecuada_2026"
    ALGORITHM: str = "HS256"
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    OTP_EXPIRE_MINUTES: int = 5
    PASSWORD_RESET_EXPIRE_MINUTES: int = 30
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    MAX_OTP_ATTEMPTS: int = 3
    OTP_RESEND_WAIT_SECONDS: int = 60
    
    MONGODB_URL: str = "mongodb://localhost:27017/?replicaSet=rs0"
    DATABASE_NAME: str = "bdg_inventario"
    
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    RECAPTCHA_SECRET_KEY: str = "test_recaptcha_secret"
    MOCK_EXTERNAL_SERVICES: bool = True
    TIMEZONE: str = "America/Guatemala"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


settings = Settings()

# Roles del sistema
ROL_ADMIN = "Administrador"
ROL_COMPRAS = "Compras"
ROL_PROVEEDOR = "Proveedor"
ROL_BODEGA = "Bodega"
ROL_CONSULTA = "Consulta"

ROLES_VALIDOS = [ROL_ADMIN, ROL_COMPRAS, ROL_PROVEEDOR, ROL_BODEGA, ROL_CONSULTA]

# Matriz de Permisos por Rol según Sección 3
PERMISOS_POR_ROL = {
    ROL_ADMIN: [
        "gestionar_usuarios",
        "gestionar_roles",
        "ver_bitacora_seguridad",
        "crear_editar_productos",
        "crear_editar_solicitudes",
        "enviar_solicitud",
        "confirmar_solicitud",
        "recibir_entrega",
        "consultar_inventario",
        "consultar_movimientos",
        "cerrar_solicitud",
    ],
    ROL_COMPRAS: [
        "crear_editar_productos",
        "crear_editar_solicitudes",
        "enviar_solicitud",
        "cerrar_solicitud",
        "consultar_inventario",
        "consultar_movimientos",
    ],
    ROL_PROVEEDOR: [
        "confirmar_solicitud",  # Solo las suyas
        "rechazar_solicitud",
        "consultar_movimientos",  # Solo sus solicitudes
    ],
    ROL_BODEGA: [
        "recibir_entrega",
        "consultar_inventario",
        "consultar_movimientos",
    ],
    ROL_CONSULTA: [
        "consultar_inventario",
        "consultar_productos",
        "consultar_movimientos",
    ],
}
