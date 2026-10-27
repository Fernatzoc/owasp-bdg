import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

// Componentes estructurales
import Layout from './components/Layout';

// Páginas (P01 a P16)
import P01_Login from './pages/P01_Login';
import P02_OtpVerification from './pages/P02_OtpVerification';
import P03_ActiveSessionAlert from './pages/P03_ActiveSessionAlert';
import P04_Register from './pages/P04_Register';
import P05_ForgotPassword from './pages/P05_ForgotPassword';
import P06_NewPassword from './pages/P06_NewPassword';
import P07_Dashboard from './pages/P07_Dashboard';
import P08_UsersRoles from './pages/P08_UsersRoles';
import P09_Products from './pages/P09_Products';
import P10_Suppliers from './pages/P10_Suppliers';
import P11_RequestsList from './pages/P11_RequestsList';
import P12_RequestForm from './pages/P12_RequestForm';
import P13_ConfirmRequest from './pages/P13_ConfirmRequest';
import P14_ReceiveDelivery from './pages/P14_ReceiveDelivery';
import P15_Inventory from './pages/P15_Inventory';
import P16_Movements from './pages/P16_Movements';

import Bitacora from './pages/Bitacora';
import VerificarEmail from './pages/VerificarEmail';
import NotFound from './pages/NotFound';

// Guardián para rutas autenticadas
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, token, loading, hasAnyRole } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !hasAnyRole(allowedRoles)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

// Guardián para rutas públicas (redirecciona a dashboard si ya está logueado)
const PublicOnlyRoute = ({ children }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-100">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (token) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Rutas Públicas */}
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <P01_Login />
              </PublicOnlyRoute>
            }
          />
          <Route path="/verificar-otp" element={<P02_OtpVerification />} />
          <Route path="/sesion-activa" element={<P03_ActiveSessionAlert />} />
          <Route
            path="/registro"
            element={
              <PublicOnlyRoute>
                <P04_Register />
              </PublicOnlyRoute>
            }
          />
          <Route path="/recuperar-contrasena" element={<P05_ForgotPassword />} />
          <Route path="/nueva-contrasena" element={<P06_NewPassword />} />
          <Route path="/verificar-email" element={<VerificarEmail />} />

          {/* Rutas Protegidas dentro de Layout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<P07_Dashboard />} />

            {/* P08 Usuarios y Roles (Admin) */}
            <Route
              path="usuarios"
              element={
                <ProtectedRoute allowedRoles={['Administrador']}>
                  <P08_UsersRoles />
                </ProtectedRoute>
              }
            />

            {/* P09 Productos */}
            <Route
              path="productos"
              element={
                <ProtectedRoute allowedRoles={['Consulta', 'Compras', 'Bodega', 'Administrador']}>
                  <P09_Products />
                </ProtectedRoute>
              }
            />

            {/* P10 Proveedores (Compras, Admin) */}
            <Route
              path="proveedores"
              element={
                <ProtectedRoute allowedRoles={['Compras', 'Administrador']}>
                  <P10_Suppliers />
                </ProtectedRoute>
              }
            />

            {/* P11 Solicitudes */}
            <Route
              path="solicitudes"
              element={
                <ProtectedRoute allowedRoles={['Compras', 'Proveedor', 'Bodega', 'Administrador']}>
                  <P11_RequestsList />
                </ProtectedRoute>
              }
            />
            {/* P12 Nueva Solicitud */}
            <Route
              path="solicitudes/nueva"
              element={
                <ProtectedRoute allowedRoles={['Compras', 'Administrador']}>
                  <P12_RequestForm />
                </ProtectedRoute>
              }
            />
            {/* P12 Editar Borrador */}
            <Route
              path="solicitudes/:id/editar"
              element={
                <ProtectedRoute allowedRoles={['Compras', 'Administrador']}>
                  <P12_RequestForm />
                </ProtectedRoute>
              }
            />
            {/* P13 Confirmar Solicitud (Proveedor, Admin) */}
            <Route
              path="solicitudes/:id/confirmar"
              element={
                <ProtectedRoute allowedRoles={['Proveedor', 'Administrador']}>
                  <P13_ConfirmRequest />
                </ProtectedRoute>
              }
            />
            {/* P14 Recibir Entrega (Bodega, Admin) */}
            <Route
              path="solicitudes/:id/recibir"
              element={
                <ProtectedRoute allowedRoles={['Bodega', 'Administrador']}>
                  <P14_ReceiveDelivery />
                </ProtectedRoute>
              }
            />

            {/* P15 Inventario */}
            <Route
              path="inventario"
              element={
                <ProtectedRoute allowedRoles={['Consulta', 'Bodega', 'Compras', 'Administrador']}>
                  <P15_Inventory />
                </ProtectedRoute>
              }
            />

            {/* P16 Movimientos */}
            <Route path="movimientos" element={<P16_Movements />} />

            {/* Bitácora de Seguridad (Admin) */}
            <Route
              path="bitacora"
              element={
                <ProtectedRoute allowedRoles={['Administrador']}>
                  <Bitacora />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
