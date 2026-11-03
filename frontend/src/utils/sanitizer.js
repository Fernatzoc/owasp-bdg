/**
 * Utilidades de sanitización y defensa en profundidad (OWASP)
 */

// Lista de campos sensibles o estructurales que NO deben ser alterados
// (evita romper contraseñas, tokens JWT, captchas y correos como admin@empresa.com)
const CAMPOS_EXCLUIDOS = new Set([
  'password',
  'confirm_password',
  'current_password',
  'new_password',
  'email',
  'token',
  'jwt',
  'captcha_token',
  'access_token',
  'refresh_token',
  'login_ticket',
  'otp'
]);

/**
 * Escapa caracteres especiales de HTML para mitigar XSS (Cross-Site Scripting).
 * Incluye comillas para proteger atributos HTML.
 */
export function escaparHTML(str) {
  if (typeof str !== 'string') return str;
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Limpia palabras reservadas comunes de inyección SQL.
 * Utiliza límites de palabra estricta (\b) y banderas insensibles a mayúsculas/minúsculas
 * para no destruir palabras legítimas del idioma español (ej. "coordinador", "orden", "señor").
 */
export function limpiarPalabrasSQL(texto) {
  if (typeof texto !== 'string') return texto;

  const palabrasReservadas = [
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WHERE', 'BETWEEN',
    'USER_INPUT', 'PASSWORD_INPUT', 'FROM', 'LIMIT',
    'DROP', 'UNION', 'EXEC', 'TRUNCATE', 'ADMIN'
  ];

  let resultado = texto;
  for (const palabra of palabrasReservadas) {
    // \b garantiza que solo se remueva la palabra exacta y aislada
    const regex = new RegExp(`\\b${palabra}\\b`, 'gi');
    resultado = resultado.replace(regex, '');
  }

  // Normalizar espacios múltiples resultantes
  return resultado.replace(/\s{2,}/g, ' ').trim();
}

/**
 * Sanitiza una cadena aplicando limpieza SQL y escape HTML
 */
export function sanitizarTexto(texto) {
  if (typeof texto !== 'string') return texto;
  return escaparHTML(limpiarPalabrasSQL(texto));
}

/**
 * Recorre recursivamente un objeto o payload de formulario sanitizando
 * todos los campos de texto, preservando intactos los campos críticos (claves, tokens, correos).
 */
export function sanitizarPayload(data) {
  if (!data || typeof data !== 'object') {
    return typeof data === 'string' ? sanitizarTexto(data) : data;
  }

  // Si es un archivo binario o FormData nativo, no alterar
  if (data instanceof FormData || data instanceof Blob || data instanceof File) {
    return data;
  }

  if (Array.isArray(data)) {
    return data.map((item) => sanitizarPayload(item));
  }

  const limpio = {};
  for (const [clave, valor] of Object.entries(data)) {
    const claveMin = clave.toLowerCase();

    if (CAMPOS_EXCLUIDOS.has(claveMin)) {
      // Dejar contraseñas, correos y tokens exactamente como fueron ingresados
      limpio[clave] = valor;
    } else if (typeof valor === 'string') {
      limpio[clave] = sanitizarTexto(valor);
    } else if (valor !== null && typeof valor === 'object') {
      limpio[clave] = sanitizarPayload(valor);
    } else {
      limpio[clave] = valor;
    }
  }

  return limpio;
}
