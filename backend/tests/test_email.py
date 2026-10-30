import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.email_service import (
    send_otp_email,
    send_verification_email,
    send_password_reset_email,
    send_lockout_warning_email,
    _send_sync_smtp,
    _send_resend_http,
    _send_brevo_http
)
from app.core.config import settings


@pytest.mark.asyncio
async def test_email_fallback_when_smtp_not_configured():
    """Verifica que sin credenciales no lance error y use el modo consola."""
    with patch.object(settings, "SMTP_USER", None), \
         patch.object(settings, "SMTP_PASSWORD", None), \
         patch.object(settings, "RESEND_API_KEY", None), \
         patch.object(settings, "BREVO_API_KEY", None):
        
        await send_otp_email("test@empresa.com", "Juan Perez", "123456")
        await send_verification_email("test@empresa.com", "Juan Perez", "dummy_token")
        await send_password_reset_email("test@empresa.com", "Juan Perez", "dummy_token")
        await send_lockout_warning_email("test@empresa.com", "Juan Perez", 15)


def test_smtp_send_success_mock():
    """Verifica que con SMTP configurado construya el mensaje y haga login/sendmail."""
    mock_smtp_instance = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_smtp_instance), \
         patch.object(settings, "SMTP_USER", "notificaciones@gmail.com"), \
         patch.object(settings, "SMTP_PASSWORD", "abcd efgh ijkl mnop"), \
         patch.object(settings, "SMTP_FROM_EMAIL", "notificaciones@gmail.com"):
        
        mock_smtp_instance.__enter__.return_value = mock_smtp_instance
        success = _send_sync_smtp(
            to_email="destinatario@gmail.com",
            subject="Prueba de Asunto",
            html_content="<h1>Hola</h1>",
            text_content="Hola"
        )

        assert success is True
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with("notificaciones@gmail.com", "abcd efgh ijkl mnop")
        mock_smtp_instance.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_resend_http_send_mock():
    """Verifica que con RESEND_API_KEY se realice la llamada POST a la API de Resend."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    with patch.object(settings, "RESEND_API_KEY", "re_test_key_123"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):

        success = await _send_resend_http(
            to_email="cliente@gmail.com",
            subject="Test Resend",
            html_content="<p>Prueba</p>",
            text_content="Prueba"
        )
        assert success is True


@pytest.mark.asyncio
async def test_brevo_http_send_mock():
    """Verifica que con BREVO_API_KEY se realice la llamada POST a la API de Brevo."""
    mock_resp = MagicMock()
    mock_resp.status_code = 201

    with patch.object(settings, "BREVO_API_KEY", "xkeysib-test-123"), \
         patch.object(settings, "BREVO_SENDER_EMAIL", "fernandotzoc4@gmail.com"), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_resp):

        success = await _send_brevo_http(
            to_email="cliente@cualquiera.com",
            subject="Test Brevo",
            html_content="<p>Prueba</p>",
            text_content="Prueba"
        )
        assert success is True
