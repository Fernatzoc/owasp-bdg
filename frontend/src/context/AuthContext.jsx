import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import api, { getDeviceId } from '../api/client';

const AuthContext = createContext(null);

const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutos según RF-SEG-06

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('bdg_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [token, setToken] = useState(() => localStorage.getItem('bdg_access_token'));
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('bdg_session_id'));
  const [loading, setLoading] = useState(true);
  const [sessionAlertMessage, setSessionAlertMessage] = useState(() => {
    const savedMsg = localStorage.getItem('bdg_session_alert');
    if (savedMsg) {
      localStorage.removeItem('bdg_session_alert');
      return savedMsg;
    }
    return null;
  });

  const lastActivityRef = useRef(Date.now());

  // Escuchar evento de sesión invalidada
  useEffect(() => {
    const handleSessionInvalidated = (event) => {
      setUser(null);
      setToken(null);
      setSessionId(null);
      setSessionAlertMessage(event.detail?.mensaje || 'Su sesión fue cerrada porque se inició en otro equipo');
    };

    window.addEventListener('session-invalidated', handleSessionInvalidated);
    setLoading(false);

    return () => {
      window.removeEventListener('session-invalidated', handleSessionInvalidated);
    };
  }, []);

  // Control de inactividad de 30 minutos (RF-SEG-06)
  useEffect(() => {
    if (!token) return;

    const updateActivity = () => {
      lastActivityRef.current = Date.now();
    };

    const events = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart'];
    events.forEach((ev) => window.addEventListener(ev, updateActivity, { passive: true }));

    const interval = setInterval(() => {
      const elapsed = Date.now() - lastActivityRef.current;
      if (elapsed >= INACTIVITY_TIMEOUT_MS) {
        // Cierre automático por inactividad a los 30 minutos
        const msg = 'Su sesión fue cerrada automáticamente por inactividad (30 minutos)';
        localStorage.removeItem('bdg_access_token');
        localStorage.removeItem('bdg_refresh_token');
        localStorage.removeItem('bdg_user');
        localStorage.removeItem('bdg_session_id');
        localStorage.setItem('bdg_session_alert', msg);

        setUser(null);
        setToken(null);
        setSessionId(null);
        setSessionAlertMessage(msg);

        // Redirigir al login
        window.location.href = '/login';
      }
    }, 15000); // Verificar cada 15 segundos

    return () => {
      events.forEach((ev) => window.removeEventListener(ev, updateActivity));
      clearInterval(interval);
    };
  }, [token]);

  const loginStep1 = async (email, password, captchaToken) => {
    const deviceId = getDeviceId();
    const response = await api.post('/auth/login', {
      email,
      password,
      captcha_token: captchaToken,
      dispositivo_id: deviceId,
    });
    return response.data;
  };

  const verifyOtp = async (loginTicket, otp, forzarCierreSesion = false) => {
    const deviceId = getDeviceId();
    const response = await api.post('/auth/verify-otp', {
      login_ticket: loginTicket,
      otp,
      dispositivo_id: deviceId,
      forzar_cierre_sesion: forzarCierreSesion,
    });

    const data = response.data;
    localStorage.setItem('bdg_access_token', data.access_token);
    localStorage.setItem('bdg_refresh_token', data.refresh_token);
    localStorage.setItem('bdg_user', JSON.stringify(data.user));
    localStorage.setItem('bdg_session_id', data.session_id);
    localStorage.removeItem('bdg_session_alert');

    setUser(data.user);
    setToken(data.access_token);
    setSessionId(data.session_id);
    setSessionAlertMessage(null);
    lastActivityRef.current = Date.now();

    return data;
  };

  const resendOtp = async (loginTicket) => {
    const response = await api.post('/auth/resend-otp', {
      login_ticket: loginTicket,
    });
    return response.data;
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (e) {
      // Ignorar error si el token ya expiró
    } finally {
      localStorage.removeItem('bdg_access_token');
      localStorage.removeItem('bdg_refresh_token');
      localStorage.removeItem('bdg_user');
      localStorage.removeItem('bdg_session_id');
      localStorage.removeItem('bdg_session_alert');
      setUser(null);
      setToken(null);
      setSessionId(null);
    }
  };

  const hasRole = (role) => {
    if (!user || !user.roles) return false;
    if (user.roles.includes('Administrador')) return true;
    return user.roles.includes(role);
  };

  const hasAnyRole = (rolesList) => {
    if (!user || !user.roles) return false;
    if (user.roles.includes('Administrador')) return true;
    return rolesList.some((r) => user.roles.includes(r));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        sessionId,
        loading,
        sessionAlertMessage,
        setSessionAlertMessage,
        loginStep1,
        verifyOtp,
        resendOtp,
        logout,
        hasRole,
        hasAnyRole,
        isAdmin: hasRole('Administrador'),
        isCompras: hasRole('Compras'),
        isProveedor: hasRole('Proveedor'),
        isBodega: hasRole('Bodega'),
        isConsulta: hasRole('Consulta'),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser utilizado dentro de un AuthProvider');
  }
  return context;
};
