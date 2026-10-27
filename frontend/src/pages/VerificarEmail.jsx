import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import api from '../api/client';
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react';

export default function VerificarEmail() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');

  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!token) {
      setLoading(false);
      setMessage('No se encontró el token de verificación en el enlace');
      return;
    }

    const verify = async () => {
      try {
        const res = await api.post('/auth/verify-email', { token });
        setSuccess(true);
        setMessage(res.data.mensaje || 'Su correo ha sido verificado con éxito');
      } catch (err) {
        setSuccess(false);
        setMessage(err.response?.data?.mensaje || 'El enlace de verificación es inválido o ha expirado');
      } finally {
        setLoading(false);
      }
    };

    verify();
  }, [token]);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-10 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200 text-center">
          {loading ? (
            <div className="py-8">
              <RefreshCw className="w-12 h-12 text-emerald-600 animate-spin mx-auto mb-4" />
              <h2 className="text-xl font-bold text-slate-800">Verificando su cuenta...</h2>
              <p className="text-sm text-slate-500 mt-1">Por favor espere un momento</p>
            </div>
          ) : success ? (
            <div>
              <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
                <CheckCircle2 className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-black text-slate-900">¡Cuenta Activada!</h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">{message}</p>
              <div className="mt-6">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center py-2.5 px-4 rounded-lg bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-700 shadow-sm"
                >
                  Iniciar Sesión
                </Link>
              </div>
            </div>
          ) : (
            <div>
              <div className="w-16 h-16 mx-auto rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mb-4">
                <XCircle className="w-10 h-10" />
              </div>
              <h2 className="text-2xl font-black text-slate-900">Error de Verificación</h2>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">{message}</p>
              <div className="mt-6">
                <Link
                  to="/login"
                  className="w-full inline-flex justify-center py-2.5 px-4 rounded-lg bg-slate-800 text-white font-bold text-sm hover:bg-slate-900 shadow-sm"
                >
                  Volver al Inicio
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
