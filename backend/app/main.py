import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    generic_http_exception_handler
)
from app.api.v1 import (
    auth,
    users,
    products,
    suppliers,
    requests,
    inventory,
    movements,
    audit
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando aplicación y conectando a base de datos...")
    await init_db()
    yield
    logger.info("Apagando aplicación...")
    await close_db()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API REST de tres capas para Gestión de Solicitudes a Proveedores e Inventario",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores de excepciones
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, generic_http_exception_handler)

# Rutas de la API v1
api_v1_router = FastAPI()
api_v1_prefix = settings.API_V1_STR

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(products.router, prefix=api_v1_prefix)
app.include_router(suppliers.router, prefix=api_v1_prefix)
app.include_router(requests.router, prefix=api_v1_prefix)
app.include_router(inventory.router, prefix=api_v1_prefix)
app.include_router(movements.router, prefix=api_v1_prefix)
app.include_router(audit.router, prefix=api_v1_prefix)


from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/health", tags=["Salud"])
@app.get(f"{api_v1_prefix}/health", tags=["Salud"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": "1.0.0"
    }

# Servir Frontend SPA compilado si existe la carpeta 'static'
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.is_dir():
    assets_dir = static_dir / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # No interceptar endpoints de API o documentación Swagger
        if (
            full_path.startswith("api/") or
            full_path.startswith("api") or
            full_path in ("docs", "redoc", "openapi.json", "health")
        ):
            raise HTTPException(status_code=404, detail="No encontrado")

        # Si el archivo estático solicitado existe (ej: favicon.ico, vite.svg)
        target_file = static_dir / full_path
        if full_path and target_file.is_file():
            return FileResponse(str(target_file))

        # En cualquier otra ruta devolver index.html para React Router SPA
        index_file = static_dir / "index.html"
        if index_file.is_file():
            return FileResponse(str(index_file))

        raise HTTPException(status_code=404, detail="Frontend no encontrado")
