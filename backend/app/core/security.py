import re
import secrets
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import bcrypt
import jwt
from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger("security")


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error verificando contraseña: {e}")
        return False


def validate_password_policy(password: str) -> None:
    """
    Valida la política de contraseñas:
    - Mínimo 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un símbolo
    """
    if len(password) < 8:
        raise AppException(
            status_code=400,
            codigo="PASSWORD_INVALIDO",
            mensaje="La contraseña debe tener al menos 8 caracteres"
        )
    if not re.search(r"[A-Z]", password):
        raise AppException(
            status_code=400,
            codigo="PASSWORD_INVALIDO",
            mensaje="La contraseña debe contener al menos una letra mayúscula"
        )
    if not re.search(r"[a-z]", password):
        raise AppException(
            status_code=400,
            codigo="PASSWORD_INVALIDO",
            mensaje="La contraseña debe contener al menos una letra minúscula"
        )
    if not re.search(r"\d", password):
        raise AppException(
            status_code=400,
            codigo="PASSWORD_INVALIDO",
            mensaje="La contraseña debe contener al menos un número"
        )
    if not re.search(r"[^A-Za-z0-9]", password):
        raise AppException(
            status_code=400,
            codigo="PASSWORD_INVALIDO",
            mensaje="La contraseña debe contener al menos un símbolo o carácter especial"
        )


def hash_token(token: str) -> str:
    """Calcula el hash SHA-256 de un código o token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_otp() -> str:
    """Genera un OTP numérico de 6 dígitos."""
    return f"{secrets.randbelow(1000000):06d}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_login_ticket(user_id: str, token_id: str, dispositivo_id: str) -> str:
    """Genera un ticket efímero firmado para el segundo paso del login (OTP)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "token_id": token_id,
        "dispositivo_id": dispositivo_id,
        "type": "login_ticket",
        "exp": expire,
        "iat": now
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AppException(
            status_code=401,
            codigo="TOKEN_EXPIRADO",
            mensaje="El token proporcionado ha expirado"
        )
    except jwt.InvalidTokenError:
        raise AppException(
            status_code=401,
            codigo="TOKEN_INVALIDO",
            mensaje="El token proporcionado es inválido"
        )


async def verify_captcha(captcha_token: Optional[str]) -> bool:
    """
    Valida el token de captcha. Para el prototipo soporta modo simulado
    o claves de prueba.
    """
    if settings.MOCK_EXTERNAL_SERVICES:
        # Modo prototipo: se acepta cualquier token o un token de prueba
        if not captcha_token or len(captcha_token.strip()) == 0:
            return False
        return True

    if not captcha_token:
        return False

    # Verificación real si no es mock
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "https://www.google.com/recaptCHA/api/siteverify",
                data={
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": captcha_token
                }
            )
            data = resp.json()
            return bool(data.get("success", False))
    except Exception as e:
        logger.error(f"Error verificando captcha con servicio externo: {e}")
        return False


def send_simulated_email(to_email: str, subject: str, content: str, code: Optional[str] = None):
    """
    Simulación de envío de correo electrónico en consola para el prototipo.
    """
    border = "=" * 60
    logger.info(
        f"\n{border}\n"
        f"✉️ [CORREO SIMULADO]\n"
        f"Para: {to_email}\n"
        f"Asunto: {subject}\n"
        + (f"CÓDIGO OTP: >>> {code} <<<\n" if code else "")
        + f"Mensaje:\n{content}\n"
        f"{border}\n"
    )
