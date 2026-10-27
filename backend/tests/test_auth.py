import pytest
from app.core.exceptions import AppException
from app.core.security import (
    validate_password_policy,
    get_password_hash,
    verify_password,
    generate_otp,
    create_access_token,
    create_login_ticket,
    decode_token,
    verify_captcha
)


def test_password_policy_valid():
    # Cumple: >=8 chars, mayúscula, minúscula, número y símbolo
    validate_password_policy("Admin123!")
    validate_password_policy("ClaveSegura@2026")


def test_password_policy_too_short():
    with pytest.raises(AppException) as exc_info:
        validate_password_policy("Ab1!xyz")
    assert exc_info.value.codigo == "PASSWORD_INVALIDO"
    assert "8 caracteres" in exc_info.value.mensaje


def test_password_policy_missing_uppercase():
    with pytest.raises(AppException) as exc_info:
        validate_password_policy("password123!")
    assert exc_info.value.codigo == "PASSWORD_INVALIDO"
    assert "mayúscula" in exc_info.value.mensaje


def test_password_policy_missing_lowercase():
    with pytest.raises(AppException) as exc_info:
        validate_password_policy("PASSWORD123!")
    assert exc_info.value.codigo == "PASSWORD_INVALIDO"
    assert "minúscula" in exc_info.value.mensaje


def test_password_policy_missing_number():
    with pytest.raises(AppException) as exc_info:
        validate_password_policy("Password!")
    assert exc_info.value.codigo == "PASSWORD_INVALIDO"
    assert "número" in exc_info.value.mensaje


def test_password_policy_missing_symbol():
    with pytest.raises(AppException) as exc_info:
        validate_password_policy("Password12345")
    assert exc_info.value.codigo == "PASSWORD_INVALIDO"
    assert "símbolo" in exc_info.value.mensaje


def test_password_hashing():
    raw_pass = "Password2026!"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_otp_generation():
    otp = generate_otp()
    assert len(otp) == 6
    assert otp.isdigit()


def test_jwt_access_token():
    payload = {"sub": "user_123", "session_id": "sess_456", "roles": ["Consulta"]}
    token = create_access_token(payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user_123"
    assert decoded["session_id"] == "sess_456"
    assert decoded["type"] == "access"


def test_login_ticket():
    ticket = create_login_ticket(
        user_id="user_789",
        token_id="tok_111",
        dispositivo_id="dev_222"
    )
    decoded = decode_token(ticket)
    assert decoded["sub"] == "user_789"
    assert decoded["token_id"] == "tok_111"
    assert decoded["dispositivo_id"] == "dev_222"
    assert decoded["type"] == "login_ticket"


@pytest.mark.asyncio
async def test_captcha_mock():
    # En modo mock / prototipo
    assert await verify_captcha("test-captcha") is True
    assert await verify_captcha("bypass-token") is True
    assert await verify_captcha("") is False
    assert await verify_captcha(None) is False
