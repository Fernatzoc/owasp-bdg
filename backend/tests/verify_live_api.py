import asyncio
import httpx
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings

BASE_URL = "http://localhost:8000/api/v1"


async def main():
    print("==================================================")
    print("🚀 INICIANDO VERIFICACIÓN COMPLETA DE LA API EN VIVO")
    print("==================================================")

    client_db = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client_db[settings.DATABASE_NAME]

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        print("\n1. Verificando Health Check...")
        res = await client.get("/health")
        assert res.status_code == 200, f"Error: {res.text}"
        print("   ✅ Health check OK:", res.json())

        # 2. Login Paso 1 (admin@empresa.com)
        print("\n2. Probando Login Paso 1 (Credenciales + Captcha)...")
        login1_payload = {
            "email": "admin@empresa.com",
            "password": "Password2026!",
            "captcha_token": "test-captcha",
            "dispositivo_id": "test-device-uuid-1"
        }
        res = await client.post("/auth/login", json=login1_payload)
        assert res.status_code == 200, f"Error en login paso 1: {res.text}"
        data1 = res.json()
        assert data1["otp_required"] is True
        login_ticket = data1["login_ticket"]
        print("   ✅ Paso 1 exitoso. Se generó login_ticket.")

        # 3. Obtener el OTP generado para el usuario desde MongoDB
        user_admin = await db.usuarios.find_one({"email": "admin@empresa.com"})
        token_doc = await db.tokens_verificacion.find_one(
            {"usuario_id": user_admin["_id"], "tipo": "otp_login", "usado": False},
            sort=[("creado_en", -1)]
        )
        assert token_doc is not None, "No se encontró token OTP en base de datos"

        # Simular lectura del OTP (buscando el hash correspondiente a los dígitos)
        # Probaremos buscar el código correcto iterando o utilizando el servicio
        from app.core.security import hash_token
        otp_encontrado = None
        for i in range(1000000):
            cand = f"{i:06d}"
            if hash_token(cand) == token_doc["codigo_hash"]:
                otp_encontrado = cand
                break

        assert otp_encontrado is not None, "No se pudo recuperar el OTP"
        print(f"   ℹ️ OTP recuperado del token de seguridad: {otp_encontrado}")

        # 4. Login Paso 2 (Validar OTP)
        print("\n3. Probando Login Paso 2 (Validar OTP y Crear Sesión)...")
        login2_payload = {
            "login_ticket": login_ticket,
            "otp": otp_encontrado,
            "dispositivo_id": "test-device-uuid-1",
            "forzar_cierre_sesion": True
        }
        res = await client.post("/auth/verify-otp", json=login2_payload)
        assert res.status_code == 200, f"Error en verify-otp: {res.text}"
        token_data = res.json()
        access_token = token_data["access_token"]
        session_id = token_data["session_id"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print(f"   ✅ Paso 2 exitoso! Sesión ID: {session_id}")
        print(f"   Roles del usuario: {token_data['user']['roles']}")

        # 5. Consultar Productos
        print("\n4. Consultando catálogo de productos...")
        res = await client.get("/products", headers=headers)
        assert res.status_code == 200
        prods = res.json()
        print(f"   ✅ Productos obtenidos: {prods['total']} productos en catálogo")
        assert prods["total"] >= 10

        # 6. Consultar Proveedores
        print("\n5. Consultando catálogo de proveedores...")
        res = await client.get("/suppliers", headers=headers)
        assert res.status_code == 200
        supps = res.json()
        print(f"   ✅ Proveedores obtenidos: {supps['total']} proveedores")
        assert supps["total"] >= 3

        # 7. Consultar Solicitudes
        print("\n6. Consultando solicitudes...")
        res = await client.get("/requests", headers=headers)
        assert res.status_code == 200
        reqs = res.json()
        print(f"   ✅ Solicitudes obtenidas: {reqs['total']} solicitudes")
        estados_vistos = {r["estado"] for r in reqs["items"]}
        print(f"   Estados presentes en solicitudes: {estados_vistos}")

        # 8. Consultar Inventario
        print("\n7. Consultando inventario disponible...")
        res = await client.get("/inventory", headers=headers)
        assert res.status_code == 200
        inv = res.json()
        print(f"   ✅ Registros de inventario: {inv['total']} ítems")

        # 9. Consultar Movimientos (Las 3 pestañas de RF-NEG-07)
        print("\n8. Consultando movimientos en sus 3 pestañas...")
        res_pedidos = await client.get("/movements?tipo=pedidos", headers=headers)
        assert res_pedidos.status_code == 200
        print(f"   ✅ Pestaña 1 (Pedidos): {res_pedidos.json()['total']} registros")

        res_ingresos = await client.get("/movements?tipo=ingresos", headers=headers)
        assert res_ingresos.status_code == 200
        print(f"   ✅ Pestaña 2 (Productos Ingresados): {res_ingresos.json()['total']} ingresos a inventario")

        res_cambios = await client.get("/movements?tipo=cambios", headers=headers)
        assert res_cambios.status_code == 200
        print(f"   ✅ Pestaña 3 (Línea de tiempo de cambios): {res_cambios.json()['total']} eventos auditables")

        # 10. Consultar Bitácora de Seguridad
        print("\n9. Consultando bitácora de seguridad...")
        res_audit = await client.get("/audit/security", headers=headers)
        assert res_audit.status_code == 200
        audits = res_audit.json()
        print(f"   ✅ Eventos en bitácora de seguridad: {audits['total']}")

        # 11. Probar Control de Roles (RBAC): Consulta no puede crear producto
        print("\n10. Verificando RBAC: Intentar crear producto sin permisos...")
        # Generar token para rol Consulta
        usr_consulta = await db.usuarios.find_one({"email": "consulta@empresa.com"})
        from app.core.security import create_access_token
        consulta_token = create_access_token({
            "sub": str(usr_consulta["_id"]),
            "session_id": session_id,  # reuse active session id for role test
            "roles": ["Consulta"]
        })
        res_unauthorized = await client.post(
            "/products",
            json={"codigo": "PROD-HACK", "nombre": "No Permitido", "unidad": "unidad"},
            headers={"Authorization": f"Bearer {consulta_token}"}
        )
        assert res_unauthorized.status_code == 403
        print("   ✅ Correcto: El rol Consulta recibió HTTP 403 al intentar crear productos")

        # 12. Probar Máquina de Estados: Transición no permitida
        print("\n11. Verificando Máquina de Estados: Transición inválida (HTTP 409)...")
        # Buscar solicitud en Borrador e intentar recibirla directamente en Bodega
        sol_borrador = await db.solicitudes.find_one({"estado": "Borrador"})
        res_invalid_trans = await client.post(
            f"/requests/{str(sol_borrador['_id'])}/receive",
            json={"lineas": [{"producto_id": str(sol_borrador["lineas"][0]["producto_id"]), "recibido": True, "cant_recibida": 5}]},
            headers=headers
        )
        assert res_invalid_trans.status_code == 409
        assert res_invalid_trans.json()["codigo"] == "TRANSICION_NO_PERMITIDA"
        print("   ✅ Correcto: Recibió HTTP 409 TRANSICION_NO_PERMITIDA al violar el ciclo de vida")

    print("\n==================================================")
    print("🎉 TODAS LAS VERIFICACIONES DE LA API EN VIVO PASARON CON ÉXITO")
    print("==================================================")
    client_db.close()

if __name__ == "__main__":
    asyncio.run(main())
