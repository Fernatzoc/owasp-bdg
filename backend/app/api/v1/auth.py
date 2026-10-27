import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, Request, Response, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.dependencies import (
    get_client_ip,
    get_device_id,
    get_current_user_and_session
)
from app.schemas.auth import (
    UserRegisterRequest,
    VerifyEmailRequest,
    LoginStep1Request,
    LoginStep1Response,
    VerifyOtpRequest,
    ResendOtpRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    RefreshTokenRequest
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/register", summary="Registro de nuevo usuario")
async def register(
    data: UserRegisterRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.register_user(db, data, ip)


@router.post("/verify-email", summary="Verificación de correo con token")
async def verify_email(
    data: VerifyEmailRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.verify_email_token(db, data.token, ip)


@router.post("/login", response_model=LoginStep1Response, summary="Inicio de sesión - Paso 1 (Credenciales + Captcha)")
async def login(
    data: LoginStep1Request,
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    # Si el cliente no mandó dispositivo_id, generamos uno y lo fijamos en cookie
    if not data.dispositivo_id or data.dispositivo_id == "desconocido":
        cookie_dev = request.cookies.get("dispositivo_id")
        if cookie_dev:
            data.dispositivo_id = cookie_dev
        else:
            data.dispositivo_id = str(uuid.uuid4())
            response.set_cookie(
                key="dispositivo_id",
                value=data.dispositivo_id,
                httponly=True,
                samesite="lax",
                max_age=365 * 24 * 3600
            )

    return await auth_service.login_step1(db, data, ip)


@router.post("/resend-otp", summary="Reenviar código OTP")
async def resend_otp(
    data: ResendOtpRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.resend_otp(db, data.login_ticket, ip)


@router.post("/verify-otp", response_model=TokenResponse, summary="Inicio de sesión - Paso 2 (Validar OTP)")
async def verify_otp(
    data: VerifyOtpRequest,
    request: Request,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent")

    token_resp = await auth_service.verify_otp_and_create_session(
        db=db,
        data=data,
        ip=ip,
        user_agent=user_agent
    )

    # Establecer cookie HttpOnly de dispositivo
    response.set_cookie(
        key="dispositivo_id",
        value=data.dispositivo_id,
        httponly=True,
        samesite="lax",
        max_age=365 * 24 * 3600
    )

    return token_resp


@router.post("/forgot-password", summary="Solicitar restablecimiento de contraseña")
async def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.forgot_password_request(db, data.email, data.captcha_token, ip)


@router.post("/reset-password", summary="Definir nueva contraseña con token de recuperación")
async def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.reset_password_with_token(
        db=db,
        token=data.token,
        new_password=data.new_password,
        confirm_password=data.confirm_password,
        ip=ip
    )


@router.post("/refresh", summary="Renovar token de acceso")
async def refresh_token(
    data: RefreshTokenRequest,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    ip = get_client_ip(request)
    return await auth_service.refresh_access_token(db, data.refresh_token, ip)


@router.post("/logout", summary="Cerrar la sesión actual")
async def logout(
    request: Request,
    response: Response,
    auth_data=Depends(get_current_user_and_session),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    user, session = auth_data
    ip = get_client_ip(request)
    res = await auth_service.logout_user(
        db=db,
        session_id=str(session["_id"]),
        user_id=str(user["_id"]),
        ip=ip
    )
    response.delete_cookie("access_token")
    return res
