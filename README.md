# Sistema de Solicitudes a Proveedores e Inventario (Full-Stack)

Prototipo funcional de 3 capas para la gestión integral de solicitudes a proveedores, confirmación de pedidos, recepción en bodega e inventario resultante, conforme a la [Especificación de Requerimientos](Especificación%20de%20Requerimientos%20–%20Sistema%20de%20Solicitudes%20a%20Proveedores%20e%20Inventario.md).

---

## 1. Arquitectura y Tecnologías

| Capa | Tecnologías | Responsabilidad |
| --- | --- | --- |
| **Frontend** | React 18, Vite, React Router v6, Tailwind CSS, Lucide Icons, Axios | 16 pantallas interactivas (P01 a P16) en español, diseño responsivo, control de vistas por rol, manejo de cookies HttpOnly y sesión de dispositivo. |
| **Backend (Capa Media)** | Python 3.12, FastAPI, Pydantic v2, Motor, PyJWT, Bcrypt | API REST asíncrona, máquina de estados estricta (8 estados), validación RBAC, control de sesión única, transacciones atómicas. |
| **Base de Datos** | MongoDB 7.0 en **Replica Set (`rs0`)** | Persistencia documental con 10 colecciones, índices únicos parciales de sesión activa, TTL de tokens y soporte ACID multi-documento. |
| **Servicios Simulados** | Email Logger en Consola, reCAPTCHA Test Keys | Notificaciones de OTP de 6 dígitos, activación de cuentas y recuperación de contraseñas visibles en consola. |

---

## 2. Pantallas del Prototipo (P01 a P16)

| # | Pantalla | Ruta | Descripción | Rol de Acceso |
|---|---|---|---|---|
| **P01** | Inicio de sesión | `/login` | Formulario con correo, contraseña, captcha simulado y enlaces a registro/recuperación. | Público |
| **P02** | Verificación OTP | `/verificar-otp` | 6 casillas numéricas, temporizador de 5:00 min, reenvío tras 60 s y conteo de intentos restantes. | Público |
| **P03** | Aviso de sesión activa | `/sesion-activa` | Alerta de sesión concurrente detectada con opciones de cerrar la otra sesión o cancelar. | Público |
| **P04** | Registro de usuario | `/registro` | Registro con medidor de fortaleza de contraseña en tiempo real, confirmación y captcha. | Público |
| **P05** | Recuperar contraseña | `/recuperar-contrasena` | Solicitud de enlace de restablecimiento con captcha y confirmación. | Público |
| **P06** | Nueva contraseña | `/nueva-contrasena` | Restablecimiento de contraseña con token temporal y reglas visibles (no repetir últimas 3). | Público |
| **P07** | Panel de inicio | `/dashboard` | Tarjetas de métricas: solicitudes por estado, entregas en próximos 7 días y alertas de stock bajo. | Todos |
| **P08** | Usuarios y roles | `/usuarios` | Gestión de usuarios, asignación de roles, vinculación a proveedor y cierre forzado de sesión. | Administrador |
| **P09** | Catálogo de productos | `/productos` | Tabla con búsqueda, filtros y modal de crear/editar productos. | Consulta, Compras, Bodega, Admin |
| **P10** | Catálogo de proveedores | `/proveedores` | Directorio de empresas proveedoras y modal de administración. | Compras, Admin |
| **P11** | Lista de solicitudes | `/solicitudes` | Tabla con número, proveedor, fecha, estado con etiqueta de color, filtros y acciones por rol. | Compras, Proveedor, Bodega, Admin |
| **P12** | Formulario de solicitud | `/solicitudes/nueva` | Creación de pedido con calendario, buscador de productos y opciones de guardar borrador o enviar. | Compras, Admin |
| **P13** | Confirmar solicitud | `/solicitudes/:id/confirmar` | Confirmación de cantidades por línea por parte del proveedor, detección de confirmación parcial y rechazo con motivo. | Proveedor, Admin |
| **P14** | Recibir entrega | `/solicitudes/:id/recibir` | Recepción física en bodega, motivo obligatorio para faltantes y cálculo automático de ingreso al inventario. | Bodega, Admin |
| **P15** | Consulta de inventario | `/inventario` | Existencias disponibles, ordenamiento por columna, paginación y exportación a CSV. | Consulta, Bodega, Compras, Admin |
| **P16** | Consulta de movimientos | `/movimientos` | 3 pestañas: **1 Pedidos**, **2 Productos ingresados**, **3 Línea de tiempo de cambios**. | Consulta, Compras, Bodega, Proveedor, Admin |

---

## 3. Despliegue con Docker Compose

### 3.1. Iniciar Todos los Servicios
Para compilar y levantar MongoDB en Replica Set, el Backend y el Frontend:

```bash
docker compose up -d
```

Servicios desplegados:
- **Frontend (React)**: [http://localhost:5173](http://localhost:5173)
- **Backend API (FastAPI)**: [http://localhost:8000](http://localhost:8000)
- **Documentación Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MongoDB Replica Set (`rs0`)**: Puerto `27017`

### 3.2. Cargar Datos de Prueba (Seed Data)
Para poblar la base de datos con los 10 productos, 3 proveedores, usuarios por cada rol y 5 solicitudes en diferentes estados:

```bash
docker compose exec backend python scripts/seed_data.py
```

---

## 4. Usuarios de Prueba y Credenciales

Contraseña común para todas las cuentas de prueba: **`Password2026!`**

| Rol | Correo Electrónico | Contraseña | Alcance de Permisos |
| --- | --- | --- | --- |
| **Administrador** | `admin@empresa.com` | `Password2026!` | Acceso irrestricto, administración de usuarios, roles y bitácora |
| **Compras** | `compras@empresa.com` | `Password2026!` | Crear y enviar solicitudes, catálogos, cerrar faltantes |
| **Proveedor** | `proveedor@empresa.com` | `Password2026!` | Ver y confirmar solicitudes dirigidas a `PROV-001` |
| **Bodega** | `bodega@empresa.com` | `Password2026!` | Registrar recepciones físicas de pedidos y actualizar inventario |
| **Consulta** | `consulta@empresa.com` | `Password2026!` | Consultar existencias, productos y movimientos (solo lectura) |

> **Nota para el inicio de sesión (OTP):** Al ingresar correo y contraseña, el backend imprimirá el código de 6 dígitos en la consola/logs del contenedor:
> ```bash
> docker compose logs -f backend
> ```

---

## 5. Despliegue en Producción en Render

Este proyecto cuenta con un `Dockerfile` multi-etapa que compila el frontend de React y lo empaqueta dentro del servidor FastAPI, permitiendo desplegar **todo el sistema en un único servicio web de Render** (plan gratuito).

### Pasos para desplegar:

1. **Crear clúster en MongoDB Atlas (Gratuito):**
   * Regístrate en [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) y crea un clúster gratuito **M0**.
   * En **Network Access**, permite el acceso desde cualquier lugar (`0.0.0.0/0`).
   * En **Database Access**, crea un usuario y contraseña.
   * Copia la cadena de conexión: `mongodb+srv://<usuario>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority`

2. **Crear el Web Service en Render:**
   * En [Render Dashboard](https://dashboard.render.com/), haz clic en **New +** > **Web Service**.
   * Conecta tu repositorio de GitHub / GitLab.
   * **Runtime:** Selecciona `Docker`.
   * **Instance Type:** `Free`.
   * **Health Check Path:** `/health`.

3. **Variables de Entorno en Render:**
   * `MONGODB_URL`: Tu cadena de conexión de MongoDB Atlas.
   * `DATABASE_NAME`: `bdg_inventario`
   * `JWT_SECRET_KEY`: Una cadena secreta segura (ej. genera una con `openssl rand -hex 32`).
   * `TIMEZONE`: `America/Guatemala`
   * `MOCK_EXTERNAL_SERVICES`: `true`

4. **Cargar Datos Iniciales (Seed Data):**
   * Una vez desplegado, ve a la pestaña **Shell** de tu servicio en Render y ejecuta:
     ```bash
     python scripts/seed_data.py
     ```
   * O puedes ejecutar el script localmente configurando temporalmente la variable `MONGODB_URL` con la cadena de Atlas.

5. **Recepción de Códigos OTP (2FA):**
   * En modo simulado (`MOCK_EXTERNAL_SERVICES=true`), al iniciar sesión el código de 6 dígitos se muestra inmediatamente en la pestaña **Logs** de Render.
