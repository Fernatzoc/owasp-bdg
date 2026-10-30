import pytest
from unittest.mock import patch, MagicMock
from app.services.email_service import (
    send_otp_email,
    send_verification_email,
    send_password_reset_email,
    send_lockout_warning_email,
    _send_sync_smtp
)
from app.core.config import settings


@pytest.mark.asyncio
async def test_email_fallback_when_smtp_not_configured():
    """Verifica que sin credenciales SMTP no lance error y use el modo consola."""
    with patch.object(settings, "SMTP_USER", None), patch.object(settings, "SMTP_PASSWORD", None):
        # No debe lanzar excepción
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
