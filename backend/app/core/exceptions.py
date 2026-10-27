from typing import Any, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        codigo: str,
        mensaje: str,
        detalles: Optional[Any] = None,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=mensaje, headers=headers)
        self.codigo = codigo
        self.mensaje = mensaje
        self.detalles = detalles


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "codigo": exc.codigo,
            "mensaje": exc.mensaje,
            "detalles": exc.detalles
        },
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    detalles = []
    for err in exc.errors():
        campo = ".".join(str(loc) for loc in err.get("loc", []))
        detalles.append({
            "campo": campo,
            "error": err.get("msg")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "codigo": "VALIDACION_FALLIDA",
            "mensaje": "Los datos enviados contienen errores de validación",
            "detalles": detalles
        }
    )


async def generic_http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    codigo_map = {
        400: "SOLICITUD_INVALIDA",
        401: "NO_AUTORIZADO",
        403: "ACCESO_DENEGADO",
        404: "NO_ENCONTRADO",
        409: "CONFLICTO",
        422: "DATOS_NO_PROCESABLES",
        500: "ERROR_INTERNO"
    }
    codigo = codigo_map.get(exc.status_code, "ERROR")
    mensaje = exc.detail if isinstance(exc.detail, str) else "Ha ocurrido un error en la solicitud"
    detalles = exc.detail if not isinstance(exc.detail, str) else None

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "codigo": codigo,
            "mensaje": mensaje,
            "detalles": detalles
        },
        headers=exc.headers
    )
