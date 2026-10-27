from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    captcha_token: str


class VerifyEmailRequest(BaseModel):
    token: str


class LoginStep1Request(BaseModel):
    email: EmailStr
    password: str
    captcha_token: str
    dispositivo_id: str


class LoginStep1Response(BaseModel):
    otp_required: bool = True
    login_ticket: str
    mensaje: str
    demo_otp: Optional[str] = None


class VerifyOtpRequest(BaseModel):
    login_ticket: str
    otp: str = Field(..., min_length=6, max_length=6)
    dispositivo_id: str
    forzar_cierre_sesion: bool = False


class ResendOtpRequest(BaseModel):
    login_ticket: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    captcha_token: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserSummary(BaseModel):
    id: str
    nombre: str
    email: str
    roles: List[str]
    proveedor_id: Optional[str] = None
    estado: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    session_id: str
    user: UserSummary


class RefreshTokenRequest(BaseModel):
    refresh_token: str
