import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import (
    get_password_hash,
    verify_password,
    validate_password_policy,
    hash_token,
    generate_otp,
    create_access_token,
    create_refresh_token,
    create_login_ticket,
    decode_token,
    verify_captcha,
    send_simulated_email
)
from app.schemas.auth import (
    UserRegisterRequest,
    LoginStep1Request,
    LoginStep1Response,
    VerifyOtpRequest,
    TokenResponse,
    UserSummary
)
from app.services.audit_service import record_audit_event


async def register_user(db: AsyncIOMotorDatabase, data: UserRegisterRequest, ip: str) -> Dict[str, Any]:
    # 1. Validar captcha
    captcha_valido = await verify_captcha(data.captcha_token)
    if not captcha_valido:
        raise AppException(
            status_code=400,
            codigo="CAPTCHA_INVALIDO",
            mensaje="La validación del captcha ha fallado"
        )

    # 2. Validar contraseñas
    if data.password != data.confirm_password:
        raise AppException(
            status_code=400,
            codigo="PASSWORD_NO_COINCIDE",
            mensaje="Las contraseñas no coinciden"
        )
    validate_password_policy(data.password)

    # 3. Validar email único
    email_normalizado = data.email.lower().strip()
    existente = await db.usuarios.find_one({"email": email_normalizado})
    if existente:
        raise AppException(
            status_code=400,
            codigo="EMAIL_DUPLICADO",
            mensaje="Ya existe una cuenta registrada con este correo electrónico"
        )

    # 4. Crear usuario en estado pendiente y rol Consulta
    password_hash = get_password_hash(data.password)
    ahora = datetime.now(timezone.utc)
    usuario_doc = {
        "nombre": data.nombre.strip(),
        "email": email_normalizado,
        "password_hash": password_hash,
        "roles": ["Consulta"],
        "proveedor_id": None,
        "estado": "pendiente",
        "intentos_fallidos": 0,
        "bloqueado_hasta": None,
        "historial_passwords": [password_hash],
        "creado_en": ahora
    }

    result = await db.usuarios.insert_one(usuario_doc)
    usuario_id = result.inserted_id

    # 5. Generar token de verificación de email (24 horas de vigencia)
    raw_token = secrets.token_urlsafe(32)
    token_doc = {
        "usuario_id": usuario_id,
        "tipo": "verificar_email",
        "codigo_hash": hash_token(raw_token),
        "intentos": 0,
        "expira_en": ahora + timedelta(hours=24),
        "usado": False,
        "creado_en": ahora
    }
    await db.tokens_verificacion.insert_one(token_doc)

    # 6. Simular envío de correo
    verify_url = f"http://localhost:5173/verificar-email?token={raw_token}"
    send_simulated_email(
        to_email=email_normalizado,
        subject="Verificación de cuenta - Sistema de Solicitudes",
        content=f"Bienvenido {data.nombre}. Para activar su cuenta haga clic en el siguiente enlace:\n{verify_url}\n(Válido por 24 horas)."
    )

    await record_audit_event(
        db=db,
        evento="REGISTRO_USUARIO",
        ip=ip,
        exito=True,
        usuario_id=str(usuario_id),
        email=email_normalizado,
        detalle="Usuario registrado exitosamente en estado pendiente"
    )

    return {
        "mensaje": "Usuario registrado exitosamente. Por favor revise su correo para verificar su cuenta.",
        "email": email_normalizado
    }


async def verify_email_token(db: AsyncIOMotorDatabase, token: str, ip: str) -> Dict[str, Any]:
    token_h = hash_token(token)
    ahora = datetime.now(timezone.utc)

    token_doc = await db.tokens_verificacion.find_one({
        "codigo_hash": token_h,
        "tipo": "verificar_email",
        "usado": False
    })

    if not token_doc:
        raise AppException(
            status_code=400,
            codigo="TOKEN_INVALIDO",
            mensaje="El token de verificación es inválido o ya ha sido utilizado"
        )

    expira_en = token_doc["expira_en"]
    if expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)

    if expira_en < ahora:
        raise AppException(
            status_code=400,
            codigo="TOKEN_EXPIRADO",
            mensaje="El enlace de verificación ha expirado. Solicite un nuevo registro o enlace."
        )

    usuario_id = token_doc["usuario_id"]
    await db.tokens_verificacion.update_one({"_id": token_doc["_id"]}, {"$set": {"usado": True}})
    await db.usuarios.update_one(
        {"_id": usuario_id},
        {"$set": {"estado": "activo"}}
    )

    usuario = await db.usuarios.find_one({"_id": usuario_id})

    await record_audit_event(
        db=db,
        evento="VERIFICACION_EMAIL",
        ip=ip,
        exito=True,
        usuario_id=str(usuario_id),
        email=usuario.get("email") if usuario else None,
        detalle="Correo verificado exitosamente. Cuenta activada."
    )

    return {"mensaje": "Su correo ha sido verificado con éxito. Ya puede iniciar sesión."}


async def login_step1(db: AsyncIOMotorDatabase, data: LoginStep1Request, ip: str) -> LoginStep1Response:
    # 1. Validar Captcha
    captcha_valido = await verify_captcha(data.captcha_token)
    if not captcha_valido:
        raise AppException(
            status_code=400,
            codigo="CAPTCHA_INVALIDO",
            mensaje="La validación del captcha ha fallado"
        )

    email_normalizado = data.email.lower().strip()
    ahora = datetime.now(timezone.utc)

    # 2. Buscar usuario
    usuario = await db.usuarios.find_one({"email": email_normalizado})
    if not usuario:
        await record_audit_event(
            db=db,
            evento="LOGIN_FALLIDO",
            ip=ip,
            exito=False,
            email=email_normalizado,
            dispositivo_id=data.dispositivo_id,
            detalle="Intento de login con email no existente"
        )
        raise AppException(
            status_code=401,
            codigo="CREDENCIALES_INVALIDAS",
            mensaje="Credenciales de acceso inválidas"
        )

    # 3. Validar si está bloqueado por intentos fallidos
    bloqueado_hasta = usuario.get("bloqueado_hasta")
    if bloqueado_hasta:
        if bloqueado_hasta.tzinfo is None:
            bloqueado_hasta = bloqueado_hasta.replace(tzinfo=timezone.utc)
        if bloqueado_hasta > ahora:
            minutos_restantes = max(1, int((bloqueado_hasta - ahora).total_seconds() // 60))
            await record_audit_event(
                db=db,
                evento="LOGIN_BLOQUEADO",
                ip=ip,
                exito=False,
                usuario_id=str(usuario["_id"]),
                email=email_normalizado,
                dispositivo_id=data.dispositivo_id,
                detalle="Cuenta temporalmente bloqueada por intentos fallidos"
            )
            raise AppException(
                status_code=403,
                codigo="CUENTA_BLOQUEADA",
                mensaje=f"La cuenta está bloqueada temporalmente por exceso de intentos fallidos. Intente nuevamente en {minutos_restantes} minuto(s)."
            )

    # 4. Validar contraseña
    password_valida = verify_password(data.password, usuario.get("password_hash", ""))
    if not password_valida:
        intentos = usuario.get("intentos_fallidos", 0) + 1
        update_fields = {"intentos_fallidos": intentos}
        bloqueado = False
        if intentos >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
            bloqueado_hasta = ahora + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            update_fields["bloqueado_hasta"] = bloqueado_hasta
            update_fields["intentos_fallidos"] = 0
            bloqueado = True

        await db.usuarios.update_one({"_id": usuario["_id"]}, {"$set": update_fields})

        await record_audit_event(
            db=db,
            evento="LOGIN_FALLIDO",
            ip=ip,
            exito=False,
            usuario_id=str(usuario["_id"]),
            email=email_normalizado,
            dispositivo_id=data.dispositivo_id,
            detalle=f"Contraseña incorrecta. Intento {intentos}. Bloqueado: {bloqueado}"
        )

        if bloqueado:
            send_simulated_email(
                to_email=email_normalizado,
                subject="Alerta de seguridad - Cuenta bloqueada temporalmente",
                content=f"Hola {usuario['nombre']}. Su cuenta ha sido bloqueada temporalmente por {settings.LOCKOUT_DURATION_MINUTES} minutos debido a 5 intentos fallidos consecutivos de inicio de sesión."
            )

        raise AppException(
            status_code=401,
            codigo="CREDENCIALES_INVALIDAS",
            mensaje="Credenciales de acceso inválidas"
        )

    # 5. Validar estado de la cuenta
    if usuario.get("estado") == "pendiente":
        raise AppException(
            status_code=403,
            codigo="CUENTA_PENDIENTE",
            mensaje="Su cuenta está pendiente de verificación por correo electrónico"
        )
    if usuario.get("estado") != "activo":
        raise AppException(
            status_code=403,
            codigo="CUENTA_INACTIVA",
            mensaje=f"La cuenta se encuentra en estado '{usuario.get('estado')}'"
        )

    # 6. Resetear intentos fallidos
    await db.usuarios.update_one(
        {"_id": usuario["_id"]},
        {"$set": {"intentos_fallidos": 0, "bloqueado_hasta": None}}
    )

    # 7. Generar código OTP de 6 dígitos
    otp_code = generate_otp()
    otp_hash = hash_token(otp_code)
    expira_otp = ahora + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    # Invalidar OTPs anteriores sin usar
    await db.tokens_verificacion.update_many(
        {"usuario_id": usuario["_id"], "tipo": "otp_login", "usado": False},
        {"$set": {"usado": True}}
    )

    token_doc = {
        "usuario_id": usuario["_id"],
        "tipo": "otp_login",
        "codigo_hash": otp_hash,
        "intentos": 0,
        "expira_en": expira_otp,
        "usado": False,
        "creado_en": ahora
    }
    result_token = await db.tokens_verificacion.insert_one(token_doc)
    token_id = str(result_token.inserted_id)

    # 8. Simular envío por correo del OTP
    send_simulated_email(
        to_email=email_normalizado,
        subject="Código de verificación de inicio de sesión (OTP)",
        content=f"Hola {usuario['nombre']}. Su código de seguridad de un solo uso es:\n{otp_code}\nEste código vence en 5 minutos y es de un solo uso.",
        code=otp_code
    )

    # 9. Generar login_ticket firmado
    login_ticket = create_login_ticket(
        user_id=str(usuario["_id"]),
        token_id=token_id,
        dispositivo_id=data.dispositivo_id
    )

    await record_audit_event(
        db=db,
        evento="OTP_ENVIADO",
        ip=ip,
        exito=True,
        usuario_id=str(usuario["_id"]),
        email=email_normalizado,
        dispositivo_id=data.dispositivo_id,
        detalle="Código OTP de 6 dígitos generado y enviado satisfactoriamente"
    )

    return LoginStep1Response(
        otp_required=True,
        login_ticket=login_ticket,
        mensaje="Se ha enviado un código de verificación a su correo",
        demo_otp=otp_code if settings.MOCK_EXTERNAL_SERVICES else None
    )


async def resend_otp(db: AsyncIOMotorDatabase, login_ticket: str, ip: str) -> Dict[str, Any]:
    payload = decode_token(login_ticket)
    if payload.get("type") != "login_ticket":
        raise AppException(
            status_code=400,
            codigo="TICKET_INVALIDO",
            mensaje="Ticket de inicio de sesión inválido"
        )

    user_id = ObjectId(payload["sub"])
    dispositivo_id = payload.get("dispositivo_id", "desconocido")
    ahora = datetime.now(timezone.utc)

    # Verificar si el último OTP fue creado hace menos de 60 segundos (RF-SEG-02)
    ultimo_token = await db.tokens_verificacion.find_one(
        {"usuario_id": user_id, "tipo": "otp_login"},
        sort=[("creado_en", -1)]
    )

    if ultimo_token and "creado_en" in ultimo_token:
        creado_en = ultimo_token["creado_en"]
        if creado_en.tzinfo is None:
            creado_en = creado_en.replace(tzinfo=timezone.utc)
        segundos_transcurridos = (ahora - creado_en).total_seconds()
        if segundos_transcurridos < settings.OTP_RESEND_WAIT_SECONDS:
            segundos_restantes = int(settings.OTP_RESEND_WAIT_SECONDS - segundos_transcurridos)
            raise AppException(
                status_code=429,
                codigo="ESPERA_REQUERIDA",
                mensaje=f"Debe esperar {segundos_restantes} segundos antes de solicitar un nuevo código OTP"
            )

    usuario = await db.usuarios.find_one({"_id": user_id})
    if not usuario:
        raise AppException(status_code=404, codigo="USUARIO_NO_EXISTE", mensaje="Usuario no encontrado")

    otp_code = generate_otp()
    otp_hash = hash_token(otp_code)
    expira_otp = ahora + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    await db.tokens_verificacion.update_many(
        {"usuario_id": user_id, "tipo": "otp_login", "usado": False},
        {"$set": {"usado": True}}
    )

    token_doc = {
        "usuario_id": user_id,
        "tipo": "otp_login",
        "codigo_hash": otp_hash,
        "intentos": 0,
        "expira_en": expira_otp,
        "usado": False,
        "creado_en": ahora
    }
    result_token = await db.tokens_verificacion.insert_one(token_doc)
    nuevo_token_id = str(result_token.inserted_id)

    send_simulated_email(
        to_email=usuario["email"],
        subject="Nuevo código de verificación OTP",
        content=f"Hola {usuario['nombre']}. Su nuevo código OTP es:\n{otp_code}\n(Vence en 5 minutos).",
        code=otp_code
    )

    nuevo_ticket = create_login_ticket(
        user_id=str(user_id),
        token_id=nuevo_token_id,
        dispositivo_id=dispositivo_id
    )

    await record_audit_event(
        db=db,
        evento="OTP_REENVIADO",
        ip=ip,
        exito=True,
        usuario_id=str(user_id),
        email=usuario["email"],
        dispositivo_id=dispositivo_id,
        detalle="Código OTP reenviado"
    )

    return {
        "mensaje": "Nuevo código de verificación enviado",
        "login_ticket": nuevo_ticket,
        "demo_otp": otp_code if settings.MOCK_EXTERNAL_SERVICES else None
    }


async def verify_otp_and_create_session(
    db: AsyncIOMotorDatabase,
    data: VerifyOtpRequest,
    ip: str,
    user_agent: Optional[str] = None
) -> TokenResponse:
    # 1. Decodificar login_ticket
    payload = decode_token(data.login_ticket)
    if payload.get("type") != "login_ticket":
        raise AppException(
            status_code=400,
            codigo="TICKET_INVALIDO",
            mensaje="Ticket de inicio de sesión inválido"
        )

    user_id = ObjectId(payload["sub"])
    token_id = ObjectId(payload["token_id"])
    dispositivo_id = data.dispositivo_id
    ahora = datetime.now(timezone.utc)

    # 2. Buscar token de verificación
    token_doc = await db.tokens_verificacion.find_one({"_id": token_id, "usado": False})
    if not token_doc:
        raise AppException(
            status_code=400,
            codigo="OTP_INVALIDO",
            mensaje="El código OTP es inválido o ya fue utilizado"
        )

    expira_en = token_doc["expira_en"]
    if expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)

    if expira_en < ahora:
        await db.tokens_verificacion.update_one({"_id": token_id}, {"$set": {"usado": True}})
        raise AppException(
            status_code=400,
            codigo="OTP_EXPIRADO",
            mensaje="El código OTP ha expirado. Por favor solicite uno nuevo."
        )

    # 3. Validar intentos máximos (máx 3 intentos)
    intentos_actuales = token_doc.get("intentos", 0)
    if intentos_actuales >= settings.MAX_OTP_ATTEMPTS:
        await db.tokens_verificacion.update_one({"_id": token_id}, {"$set": {"usado": True}})
        raise AppException(
            status_code=400,
            codigo="OTP_BLOQUEADO",
            mensaje="Ha excedido el número máximo de intentos para este código OTP. Solicite un nuevo código."
        )

    # 4. Validar coincidencia de código
    codigo_ingresado_hash = hash_token(data.otp.strip())
    if codigo_ingresado_hash != token_doc["codigo_hash"]:
        nuevos_intentos = intentos_actuales + 1
        await db.tokens_verificacion.update_one(
            {"_id": token_id},
            {"$set": {"intentos": nuevos_intentos}}
        )
        intentos_restantes = max(0, settings.MAX_OTP_ATTEMPTS - nuevos_intentos)
        raise AppException(
            status_code=400,
            codigo="OTP_INCORRECTO",
            mensaje=f"Código de verificación incorrecto. Le quedan {intentos_restantes} intento(s)."
        )

    # 5. Obtener usuario
    usuario = await db.usuarios.find_one({"_id": user_id})
    if not usuario:
        raise AppException(status_code=404, codigo="USUARIO_NO_EXISTE", mensaje="Usuario no encontrado")

    # 6. Regla de Sesión Única (RF-SEG-06):
    # - Un usuario solo puede tener una sesión activa en el sistema.
    #   Si inicia sesión en OTRO equipo/navegador, se le advierte y se invalida la anterior al confirmar.
    # - Un mismo equipo/navegador solo puede tener una sesión activa a la vez:
    #   Si ya hay una sesión de OTRO usuario en ese equipo, se le advierte.
    sesion_otro_dispositivo = await db.sesiones.find_one({
        "usuario_id": user_id,
        "dispositivo_id": {"$ne": dispositivo_id},
        "activa": True,
        "expira_en": {"$gt": ahora}
    })

    sesion_otro_usuario = await db.sesiones.find_one({
        "dispositivo_id": dispositivo_id,
        "usuario_id": {"$ne": user_id},
        "activa": True,
        "expira_en": {"$gt": ahora}
    })

    hay_conflicto_sesion = (sesion_otro_dispositivo is not None) or (sesion_otro_usuario is not None)

    if hay_conflicto_sesion and not data.forzar_cierre_sesion:
        # IMPORTANTE: NO quemar el token todavía para permitir al usuario confirmar en P03
        motivo = "usuario" if sesion_otro_dispositivo else "dispositivo"
        raise AppException(
            status_code=409,
            codigo="SESION_ACTIVA_EXISTENTE",
            mensaje="Ya existe una sesión activa.",
            detalles={
                "tipo_conflicto": motivo,
                "mensaje": "Ya existe una sesión abierta en otro equipo o en este navegador. ¿Desea cerrar la otra sesión para continuar?"
            }
        )

    # Marcar OTP como usado solo cuando ya se procede a crear la sesión
    await db.tokens_verificacion.update_one({"_id": token_id}, {"$set": {"usado": True}})

    # Si forzar_cierre_sesion es True o no hay sesión activa previa:
    # Invalidar sesiones activas previas del usuario y del dispositivo
    await db.sesiones.update_many(
        {"$or": [{"usuario_id": user_id}, {"dispositivo_id": dispositivo_id}], "activa": True},
        {"$set": {"activa": False}}
    )

    # 7. Crear nueva sesión activa
    expira_sesion = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    sesion_doc = {
        "usuario_id": user_id,
        "dispositivo_id": dispositivo_id,
        "ip": ip,
        "user_agent": user_agent,
        "refresh_token_hash": None,
        "activa": True,
        "creada_en": ahora,
        "ultimo_acceso": ahora,
        "expira_en": expira_sesion
    }
    result_sesion = await db.sesiones.insert_one(sesion_doc)
    session_id = str(result_sesion.inserted_id)

    # 8. Generar tokens JWT
    jwt_data = {
        "sub": str(user_id),
        "session_id": session_id,
        "roles": usuario.get("roles", ["Consulta"]),
        "email": usuario["email"],
        "nombre": usuario["nombre"]
    }
    access_token = create_access_token(jwt_data)
    refresh_token = create_refresh_token({"sub": str(user_id), "session_id": session_id})

    # Guardar hash de refresh token
    await db.sesiones.update_one(
        {"_id": result_sesion.inserted_id},
        {"$set": {"refresh_token_hash": hash_token(refresh_token)}}
    )

    await record_audit_event(
        db=db,
        evento="LOGIN_EXITOSO",
        ip=ip,
        exito=True,
        usuario_id=str(user_id),
        email=usuario["email"],
        dispositivo_id=dispositivo_id,
        detalle=f"Inicio de sesión completado satisfactoriamente. Sesión ID: {session_id}"
    )

    user_summary = UserSummary(
        id=str(usuario["_id"]),
        nombre=usuario["nombre"],
        email=usuario["email"],
        roles=usuario.get("roles", ["Consulta"]),
        proveedor_id=str(usuario["proveedor_id"]) if usuario.get("proveedor_id") else None,
        estado=usuario.get("estado", "activo")
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        session_id=session_id,
        user=user_summary
    )


async def forgot_password_request(db: AsyncIOMotorDatabase, email: str, captcha_token: str, ip: str) -> Dict[str, Any]:
    captcha_valido = await verify_captcha(captcha_token)
    if not captcha_valido:
        raise AppException(
            status_code=400,
            codigo="CAPTCHA_INVALIDO",
            mensaje="La validación del captcha ha fallado"
        )

    email_normalizado = email.lower().strip()
    usuario = await db.usuarios.find_one({"email": email_normalizado})
    ahora = datetime.now(timezone.utc)

    if usuario:
        # Generar token de recuperación con vigencia de 30 minutos
        raw_token = secrets.token_urlsafe(32)
        token_doc = {
            "usuario_id": usuario["_id"],
            "tipo": "reset_password",
            "codigo_hash": hash_token(raw_token),
            "intentos": 0,
            "expira_en": ahora + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
            "usado": False,
            "creado_en": ahora
        }
        await db.tokens_verificacion.insert_one(token_doc)

        reset_url = f"http://localhost:5173/nueva-contrasena?token={raw_token}"
        send_simulated_email(
            to_email=email_normalizado,
            subject="Recuperación de contraseña - Sistema de Solicitudes",
            content=f"Hola {usuario['nombre']}. Ha solicitado restablecer su contraseña.\nHaga clic en el siguiente enlace:\n{reset_url}\n(Vigencia de 30 minutos)."
        )

        await record_audit_event(
            db=db,
            evento="SOLICITUD_RESET_PASSWORD",
            ip=ip,
            exito=True,
            usuario_id=str(usuario["_id"]),
            email=email_normalizado,
            detalle="Enlace de recuperación generado y enviado por correo"
        )
    else:
        # No revelar si el correo existe
        await record_audit_event(
            db=db,
            evento="SOLICITUD_RESET_PASSWORD",
            ip=ip,
            exito=False,
            email=email_normalizado,
            detalle="Solicitud de reset para email no registrado"
        )

    return {
        "mensaje": "Si el correo está registrado en nuestro sistema, recibirá un enlace para restablecer su contraseña."
    }


async def reset_password_with_token(
    db: AsyncIOMotorDatabase,
    token: str,
    new_password: str,
    confirm_password: str,
    ip: str
) -> Dict[str, Any]:
    if new_password != confirm_password:
        raise AppException(
            status_code=400,
            codigo="PASSWORD_NO_COINCIDE",
            mensaje="Las contraseñas no coinciden"
        )
    validate_password_policy(new_password)

    token_h = hash_token(token)
    ahora = datetime.now(timezone.utc)

    token_doc = await db.tokens_verificacion.find_one({
        "codigo_hash": token_h,
        "tipo": "reset_password",
        "usado": False
    })

    if not token_doc:
        raise AppException(
            status_code=400,
            codigo="TOKEN_INVALIDO",
            mensaje="El enlace de recuperación es inválido o ya ha sido utilizado"
        )

    expira_en = token_doc["expira_en"]
    if expira_en.tzinfo is None:
        expira_en = expira_en.replace(tzinfo=timezone.utc)

    if expira_en < ahora:
        await db.tokens_verificacion.update_one({"_id": token_doc["_id"]}, {"$set": {"usado": True}})
        raise AppException(
            status_code=400,
            codigo="TOKEN_EXPIRADO",
            mensaje="El enlace de recuperación ha expirado. Por favor solicite uno nuevo."
        )

    usuario_id = token_doc["usuario_id"]
    usuario = await db.usuarios.find_one({"_id": usuario_id})
    if not usuario:
        raise AppException(status_code=404, codigo="USUARIO_NO_EXISTE", mensaje="Usuario no encontrado")

    # Validar que no repita las últimas 3 contraseñas (RF-SEG-04)
    historial = usuario.get("historial_passwords", [])
    for old_hash in historial[-3:]:
        if verify_password(new_password, old_hash):
            raise AppException(
                status_code=400,
                codigo="PASSWORD_REPETIDA",
                mensaje="La nueva contraseña no puede coincidir con ninguna de las últimas 3 contraseñas utilizadas"
            )

    new_hash = get_password_hash(new_password)
    historial.append(new_hash)
    historial = historial[-5:]  # Guardar hasta 5 para mantener historial limpio

    # Actualizar contraseña y resetear intentos
    await db.usuarios.update_one(
        {"_id": usuario_id},
        {"$set": {
            "password_hash": new_hash,
            "historial_passwords": historial,
            "intentos_fallidos": 0,
            "bloqueado_hasta": None
        }}
    )

    # Quemar el token usado
    await db.tokens_verificacion.update_one({"_id": token_doc["_id"]}, {"$set": {"usado": True}})

    # Cerrar todas las sesiones activas del usuario (RF-SEG-04 regla 4)
    await db.sesiones.update_many(
        {"usuario_id": usuario_id, "activa": True},
        {"$set": {"activa": False}}
    )

    # Notificar por correo
    send_simulated_email(
        to_email=usuario["email"],
        subject="Contraseña actualizada exitosamente",
        content=f"Hola {usuario['nombre']}. Su contraseña ha sido modificada. Por seguridad, todas las sesiones activas han sido cerradas."
    )

    await record_audit_event(
        db=db,
        evento="CAMBIO_PASSWORD",
        ip=ip,
        exito=True,
        usuario_id=str(usuario_id),
        email=usuario["email"],
        detalle="Contraseña restablecida correctamente. Todas las sesiones activas fueron cerradas."
    )

    return {"mensaje": "Su contraseña ha sido actualizada con éxito. Inicie sesión con su nueva contraseña."}


async def refresh_access_token(db: AsyncIOMotorDatabase, refresh_token: str, ip: str) -> Dict[str, str]:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise AppException(status_code=401, codigo="TOKEN_INVALIDO", mensaje="Token de refresco inválido")

    user_id = ObjectId(payload["sub"])
    session_id = ObjectId(payload["session_id"])
    ahora = datetime.now(timezone.utc)

    session = await db.sesiones.find_one({"_id": session_id, "activa": True})
    if not session:
        raise AppException(
            status_code=401,
            codigo="SESION_INVALIDADA",
            mensaje="La sesión ha expirado o ya no está activa"
        )

    # Validar hash de refresh token
    if session.get("refresh_token_hash") != hash_token(refresh_token):
        await db.sesiones.update_one({"_id": session_id}, {"$set": {"activa": False}})
        raise AppException(
            status_code=401,
            codigo="TOKEN_REVOCADO",
            mensaje="Token de refresco revocado"
        )

    usuario = await db.usuarios.find_one({"_id": user_id, "estado": "activo"})
    if not usuario:
        raise AppException(status_code=401, codigo="USUARIO_INACTIVO", mensaje="Usuario inactivo o no encontrado")

    # Renovar expiración de sesión
    nueva_expiracion = ahora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    await db.sesiones.update_one(
        {"_id": session_id},
        {"$set": {"ultimo_acceso": ahora, "expira_en": nueva_expiracion}}
    )

    jwt_data = {
        "sub": str(user_id),
        "session_id": str(session_id),
        "roles": usuario.get("roles", ["Consulta"]),
        "email": usuario["email"],
        "nombre": usuario["nombre"]
    }
    nuevo_access_token = create_access_token(jwt_data)

    return {
        "access_token": nuevo_access_token,
        "token_type": "bearer"
    }


async def logout_user(db: AsyncIOMotorDatabase, session_id: str, user_id: str, ip: str) -> Dict[str, str]:
    if ObjectId.is_valid(session_id):
        await db.sesiones.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": {"activa": False}}
        )

    await record_audit_event(
        db=db,
        evento="LOGOUT",
        ip=ip,
        exito=True,
        usuario_id=user_id,
        detalle="Cierre de sesión voluntario"
    )

    return {"mensaje": "Sesión cerrada satisfactoriamente"}
