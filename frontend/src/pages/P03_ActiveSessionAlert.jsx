import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { AlertTriangle, LogOut, X } from 'lucide-react';

export default function P03_ActiveSessionAlert() {
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyOtp } = useAuth();

  const loginTicket = location.state?.loginTicket;
  const otp = location.state?.otp;
  const email = location.state?.email;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!loginTicket || !otp) {
    navigate('/login');
    return null;
  }

  const handleForceLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      // Invalida la sesión anterior y abre la nueva sesión en este equipo (RF-SEG-06)
      await verifyOtp(loginTicket, otp, true);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.mensaje || 'Error al cerrar la sesión existente');
      setLoading(false);
    }
  };

  const handleCancel = () => {
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center font-bold shadow-sm">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="mt-4 text-center text-2xl font-black tracking-tight text-slate-900">
          Ya existe una sesión activa
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600 px-4">
          Por motivos de seguridad, solo se permite una sesión activa en el sistema.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
              {error}
            </div>
          )}

          <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-xl mb-6 text-sm text-amber-900 leading-relaxed">
            Se ha detectado una sesión abierta para <span className="font-semibold">{email}</span> en otro equipo o navegador.
            <div className="mt-2 text-xs text-amber-700">
              Si decide continuar, la sesión anterior será cerrada de inmediato y este equipo pasará a ser el autorizado.
            </div>
          </div>

          <div className="space-y-3">
            <button
              onClick={handleForceLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-amber-600 hover:bg-amber-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500 disabled:opacity-50 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {loading ? 'Cerrando sesión previa...' : 'Cerrar la otra sesión y continuar'}
            </button>

            <button
              onClick={handleCancel}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 border border-slate-300 rounded-lg text-sm font-medium text-slate-700 bg-white hover:bg-slate-50 transition-colors"
            >
              <X className="w-4 h-4 text-slate-400" />
              Cancelar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
