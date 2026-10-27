import axios from 'axios';

// Función para obtener o inicializar el ID persistente del dispositivo
export const getDeviceId = () => {
  let deviceId = localStorage.getItem('bdg_device_id');
  if (!deviceId) {
    deviceId = 'dev-' + crypto.randomUUID();
    localStorage.setItem('bdg_device_id', deviceId);
  }
  return deviceId;
};

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('bdg_access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    config.headers['X-Device-Id'] = getDeviceId();
    return config;
  },
  (error) => Promise.reject(error)
);

// Variable para evitar bucles de refresco infinito
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const status = error.response?.status;
    const data = error.response?.data;
    const codigo = data?.codigo;

    // Manejar error 401 (No autorizado, token expirado, sesión invalidada o cerrada)
    if (status === 401 && !originalRequest._retry) {
      const isAuthEndpoint = originalRequest.url?.includes('/auth/login') ||
                             originalRequest.url?.includes('/auth/verify-otp') ||
                             originalRequest.url?.includes('/auth/refresh');

      // Intentar refrescar token si tenemos un refresh_token y no es un endpoint de login
      const refreshToken = localStorage.getItem('bdg_refresh_token');
      if (!isAuthEndpoint && refreshToken && codigo === 'TOKEN_EXPIRADO') {
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            failedQueue.push({ resolve, reject });
          })
            .then((token) => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return api(originalRequest);
            })
            .catch((err) => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
          const refreshRes = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken
          }, {
            headers: { 'X-Device-Id': getDeviceId() }
          });

          const newAccessToken = refreshRes.data.access_token;
          localStorage.setItem('bdg_access_token', newAccessToken);
          api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`;
          processQueue(null, newAccessToken);
          isRefreshing = false;

          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return api(originalRequest);
        } catch (refreshErr) {
          processQueue(refreshErr, null);
          isRefreshing = false;
          // El refresco falló: la sesión ha muerto
        }
      }

      // Si no se puede refrescar o la sesión fue explícitamente invalidada:
      // Determinar mensaje descriptivo según especificación
      let mensaje = data?.mensaje || 'Su sesión ha expirado o fue cerrada en otro equipo';
      if (codigo === 'SESION_INVALIDADA') {
        mensaje = data?.mensaje || 'Su sesión fue cerrada porque se inició en otro equipo';
      } else if (codigo === 'TOKEN_EXPIRADO') {
        mensaje = 'Su sesión ha expirado por inactividad. Por favor ingrese de nuevo.';
      }

      // Limpiar almacenamiento local
      localStorage.removeItem('bdg_access_token');
      localStorage.removeItem('bdg_refresh_token');
      localStorage.removeItem('bdg_user');
      localStorage.removeItem('bdg_session_id');
      localStorage.setItem('bdg_session_alert', mensaje);

      window.dispatchEvent(new CustomEvent('session-invalidated', {
        detail: { mensaje }
      }));

      // Si no estamos en páginas públicas de auth, redirigir de inmediato al login
      const currentPath = window.location.pathname;
      const publicPaths = ['/login', '/registro', '/recuperar-contrasena', '/nueva-contrasena', '/verificar-otp', '/sesion-activa'];
      if (!publicPaths.some(p => currentPath.startsWith(p))) {
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
