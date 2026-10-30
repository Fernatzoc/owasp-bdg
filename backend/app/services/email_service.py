import asyncio
import logging
import smtplib
import httpx
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _send_resend_http(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Envío de correo mediante la API REST HTTPS de Resend (Puerto 443 - Compatible con Render Free)."""
    try:
        from_email = settings.RESEND_FROM or "Sistema de Inventario <onboarding@resend.dev>"
        headers = {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "from": from_email,
            "to": [to_email],
            "subject": subject,
            "html": html_content,
            "text": text_content
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post("https://api.resend.com/emails", json=payload, headers=headers)
            if resp.status_code in (200, 201):
                logger.info(f"✉️ Correo enviado exitosamente a {to_email} vía Resend HTTPS API.")
                return True
            else:
                logger.error(f"❌ Error al enviar correo vía Resend API ({resp.status_code}): {resp.text}")
                return False
    except Exception as e:
        logger.error(f"❌ Excepción conectando a Resend API: {e}")
        return False


def _send_sync_smtp(to_email: str, subject: str, html_content: str, text_content: str) -> bool:
    """Envío síncrono de correo mediante smtplib (ejecutado en hilo separado)."""
    from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    from_name = settings.SMTP_FROM_NAME

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    part_text = MIMEText(text_content, "plain", "utf-8")
    part_html = MIMEText(html_content, "html", "utf-8")
    msg.attach(part_text)
    msg.attach(part_html)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(from_email, [to_email], msg.as_string())
        logger.info(f"✉️ Correo enviado exitosamente a {to_email} vía Gmail SMTP.")
        return True
    except Exception as e:
        logger.error(f"❌ Error al enviar correo vía SMTP a {to_email}: {e}")
        return False


def _log_simulated_email(to_email: str, subject: str, content: str, code: Optional[str] = None):
    """Respaldo para desarrollo o cuando SMTP/Resend no están configurados."""
    border = "=" * 60
    logger.info(
        f"\n{border}\n"
        f"✉️ [CORREO - MODO CONSOLA]\n"
        f"Para: {to_email}\n"
        f"Asunto: {subject}\n"
        + (f"CÓDIGO OTP: >>> {code} <<<\n" if code else "")
        + f"Mensaje:\n{content}\n"
        f"{border}\n"
    )


async def send_email(to_email: str, subject: str, html_content: str, text_content: str, code: Optional[str] = None) -> bool:
    """
    Envía un correo electrónico.
    Prioridad:
    1. Si RESEND_API_KEY está configurado -> Resend HTTPS API (puerto 443, ideal para Render Free).
    2. Si SMTP_USER y SMTP_PASSWORD están configurados -> Gmail SMTP (puerto 587).
    3. Respaldo a consola si ninguno está configurado o si ocurre un fallo.
    """
    # 1. Intentar con Resend (HTTPS / Puerto 443)
    if settings.RESEND_API_KEY:
        success = await _send_resend_http(to_email, subject, html_content, text_content)
        if success:
            return True
        logger.warning("Fallo en envío vía Resend API, recurriendo a respaldo en consola...")

    # 2. Intentar con Gmail SMTP (si está configurado)
    elif settings.SMTP_USER and settings.SMTP_PASSWORD:
        success = await asyncio.to_thread(_send_sync_smtp, to_email, subject, html_content, text_content)
        if success:
            return True
        logger.warning("Fallo en envío SMTP, recurriendo a respaldo en consola...")

    # 3. Fallback / Desarrollo
    _log_simulated_email(to_email, subject, text_content, code=code)
    return False


def _get_base_template(titulo: str, contenido_html: str) -> str:
    """Plantilla base HTML con diseño limpio y responsive."""
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; color: #1e293b; }}
    .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0; }}
    .header {{ background: #059669; padding: 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.025em; }}
    .header p {{ margin: 4px 0 0; font-size: 13px; opacity: 0.9; }}
    .content {{ padding: 32px 28px; }}
    .otp-box {{ background: #f0fdf4; border: 2px dashed #86efac; border-radius: 12px; padding: 20px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-family: 'Courier New', Courier, monospace; font-size: 34px; font-weight: 800; letter-spacing: 8px; color: #15803d; margin: 0; }}
    .btn {{ display: inline-block; background: #059669; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 10px; font-weight: bold; font-size: 14px; text-align: center; margin: 20px 0; }}
    .footer {{ background: #f8fafc; padding: 20px 28px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
    .badge-warn {{ background: #fef3c7; color: #92400e; padding: 10px 14px; border-radius: 8px; font-size: 12px; margin-top: 16px; text-align: left; border-left: 4px solid #f59e0b; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Sistema de Solicitudes a Proveedores e Inventario</h1>
      <p>Notificación Oficial de Seguridad</p>
    </div>
    <div class="content">
      {contenido_html}
    </div>
    <div class="footer">
      <p>Este es un correo automático generado por el Sistema de Inventario BDG.<br>Por favor no responda a este mensaje.</p>
    </div>
  </div>
</body>
</html>"""


async def send_otp_email(to_email: str, user_name: str, otp_code: str):
    """Envía el código de verificación en 2 pasos (OTP)."""
    subject = f"{otp_code} es su código de verificación - Sistema de Inventario"
    html_content = _get_base_template(
        "Código de Verificación OTP",
        f"""
        <h2 style="font-size: 18px; margin-top: 0; color: #0f172a;">Hola, {user_name}</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          Ha solicitado iniciar sesión en el <strong>Sistema de Solicitudes e Inventario</strong>. Use el siguiente código de un solo uso (OTP) para completar su autenticación:
        </p>
        <div class="otp-box">
          <p class="otp-code">{otp_code}</p>
          <p style="margin: 8px 0 0; font-size: 12px; color: #166534; font-weight: 600;">Válido por 5 minutos (1 solo uso)</p>
        </div>
        <div class="badge-warn">
          <strong>⚠️ Aviso de Seguridad:</strong> Si usted no intentó iniciar sesión, cambie su contraseña de inmediato y notifique al Administrador del sistema.
        </div>
        """
    )
    text_content = (
        f"Hola {user_name}.\n\n"
        f"Su código de verificación OTP es: {otp_code}\n\n"
        f"Este código es válido por 5 minutos y expira al utilizarse.\n"
        f"Si no intentó iniciar sesión, comuníquese con el administrador."
    )
    await send_email(to_email, subject, html_content, text_content, code=otp_code)


async def send_verification_email(to_email: str, user_name: str, token: str):
    """Envía el enlace de activación de cuenta tras el registro."""
    subject = "Active su cuenta - Sistema de Solicitudes e Inventario"
    frontend_base = settings.FRONTEND_URL.rstrip("/")
    activation_url = f"{frontend_base}/verificar-email?token={token}"

    html_content = _get_base_template(
        "Confirmación de Cuenta",
        f"""
        <h2 style="font-size: 18px; margin-top: 0; color: #0f172a;">¡Bienvenido/a, {user_name}!</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          Gracias por registrarse en el <strong>Sistema de Solicitudes a Proveedores e Inventario</strong>. Para activar su cuenta y comenzar a utilizar la plataforma, haga clic en el siguiente botón:
        </p>
        <div style="text-align: center;">
          <a href="{activation_url}" class="btn">Activar Mi Cuenta</a>
        </div>
        <p style="font-size: 12px; color: #64748b; word-break: break-all;">
          Si el botón no funciona, copie y pegue este enlace en su navegador:<br>
          <a href="{activation_url}" style="color: #059669;">{activation_url}</a>
        </p>
        <div class="badge-warn">
          Este enlace tiene una vigencia de <strong>24 horas</strong>. Su cuenta tendrá asignado inicialmente el rol de <em>Consulta</em>.
        </div>
        """
    )
    text_content = (
        f"¡Bienvenido/a {user_name}!\n\n"
        f"Para activar su cuenta haga clic en el siguiente enlace:\n{activation_url}\n\n"
        f"(Este enlace vence en 24 horas)."
    )
    await send_email(to_email, subject, html_content, text_content)


async def send_password_reset_email(to_email: str, user_name: str, token: str):
    """Envía el enlace para restablecer la contraseña olvidada."""
    subject = "Recuperación de Contraseña - Sistema de Inventario"
    frontend_base = settings.FRONTEND_URL.rstrip("/")
    reset_url = f"{frontend_base}/nueva-contrasena?token={token}"

    html_content = _get_base_template(
        "Recuperar Contraseña",
        f"""
        <h2 style="font-size: 18px; margin-top: 0; color: #0f172a;">Hola, {user_name}</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          Hemos recibido una solicitud para restablecer la contraseña de su cuenta. Para definir una nueva clave segura, haga clic en el siguiente botón:
        </p>
        <div style="text-align: center;">
          <a href="{reset_url}" class="btn">Restablecer Mi Contraseña</a>
        </div>
        <p style="font-size: 12px; color: #64748b; word-break: break-all;">
          Si el botón no funciona, copie este enlace:<br>
          <a href="{reset_url}" style="color: #059669;">{reset_url}</a>
        </p>
        <div class="badge-warn">
          <strong>Importante:</strong> Este enlace expira en <strong>30 minutos</strong> y todas sus sesiones activas serán cerradas al actualizar la contraseña.
        </div>
        """
    )
    text_content = (
        f"Hola {user_name}.\n\n"
        f"Para restablecer su contraseña ingrese al siguiente enlace:\n{reset_url}\n\n"
        f"(Válido por 30 minutos)."
    )
    await send_email(to_email, subject, html_content, text_content)


async def send_lockout_warning_email(to_email: str, user_name: str, duration_minutes: int):
    """Notifica al usuario que su cuenta ha sido bloqueada temporalmente por intentos fallidos."""
    subject = "⚠️ Alerta de Seguridad: Cuenta bloqueada temporalmente"
    html_content = _get_base_template(
        "Alerta de Seguridad",
        f"""
        <h2 style="font-size: 18px; margin-top: 0; color: #dc2626;">Alerta de Seguridad</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          Estimado/a <strong>{user_name}</strong>, le informamos que su cuenta ha sido bloqueada temporalmente durante <strong>{duration_minutes} minutos</strong> debido a 5 intentos consecutivos fallidos de inicio de sesión.
        </p>
        <div class="badge-warn">
          Si usted no realizó estos intentos, es posible que alguien esté intentando adivinar su contraseña. Le recomendamos restablecerla en cuanto su cuenta vuelva a estar activa.
        </div>
        """
    )
    text_content = (
        f"Alerta de Seguridad\n\n"
        f"Estimado/a {user_name}, su cuenta ha sido bloqueada temporalmente por {duration_minutes} minutos debido a 5 intentos fallidos consecutivos de inicio de sesión."
    )
    await send_email(to_email, subject, html_content, text_content)


async def send_request_notification_email(to_email: str, recipient_name: str, subject_text: str, message_text: str):
    """Notificaciones sobre cambios en solicitudes a proveedores."""
    subject = f"Actualización de Solicitud: {subject_text}"
    html_content = _get_base_template(
        "Actualización de Solicitud",
        f"""
        <h2 style="font-size: 18px; margin-top: 0; color: #0f172a;">Estimado/a {recipient_name}</h2>
        <p style="font-size: 14px; line-height: 1.6; color: #475569;">
          {message_text}
        </p>
        <div style="text-align: center;">
          <a href="{settings.FRONTEND_URL}" class="btn">Ir al Sistema</a>
        </div>
        """
    )
    await send_email(to_email, subject, html_content, message_text)
