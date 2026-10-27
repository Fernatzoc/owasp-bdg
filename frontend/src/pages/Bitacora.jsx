import React, { useState, useEffect } from 'react';
import api from '../api/client';
import Toast from '../components/Toast';
import { ShieldAlert, Search, CheckCircle2, XCircle, Clock, Laptop } from 'lucide-react';

export default function Bitacora() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  const [eventoFilter, setEventoFilter] = useState('');
  const [emailFilter, setEmailFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchLogs();
  }, [page]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (eventoFilter) params.append('evento', eventoFilter);
      if (emailFilter) params.append('email', emailFilter);
      params.append('page', page.toString());
      params.append('size', '25');

      const res = await api.get(`/audit/security?${params.toString()}`);
      setLogs(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.pages || 1);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando bitácora de seguridad' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
          <ShieldAlert className="w-7 h-7 text-emerald-600" />
          Bitácora de Auditoría y Seguridad
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Registro inmutable de accesos, intentos fallidos, cambios de credenciales y administración
        </p>
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Filtrar por correo de usuario..."
            value={emailFilter}
            onChange={(e) => setEmailFilter(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <select
          value={eventoFilter}
          onChange={(e) => setEventoFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos los eventos</option>
          <option value="LOGIN_EXITOSO">LOGIN_EXITOSO</option>
          <option value="LOGIN_FALLIDO">LOGIN_FALLIDO</option>
          <option value="OTP_ENVIADO">OTP_ENVIADO</option>
          <option value="OTP_REENVIADO">OTP_REENVIADO</option>
          <option value="CAMBIO_PASSWORD">CAMBIO_PASSWORD</option>
          <option value="ROLES_MODIFICADOS">ROLES_MODIFICADOS</option>
          <option value="SESION_FORZADA_CERRADA">SESION_FORZADA_CERRADA</option>
          <option value="LOGOUT">LOGOUT</option>
        </select>

        <button
          onClick={() => {
            setPage(1);
            fetchLogs();
          }}
          className="px-5 py-2 bg-slate-800 text-white font-bold text-sm rounded-lg hover:bg-slate-900"
        >
          Filtrar
        </button>
      </div>

      {/* Tabla */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-sm">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Fecha y Hora</th>
                <th className="py-3 px-4">Evento</th>
                <th className="py-3 px-4">Usuario / Email</th>
                <th className="py-3 px-4">IP / Dispositivo</th>
                <th className="py-3 px-4 text-center">Resultado</th>
                <th className="py-3 px-4">Detalle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    Cargando bitácora...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No hay eventos registrados
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3 px-4 text-xs text-slate-600 font-mono">
                      {new Date(log.fecha).toLocaleString('es-GT')}
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-xs text-slate-800">
                      {log.evento}
                    </td>
                    <td className="py-3 px-4 text-xs font-semibold text-slate-700">
                      {log.email || '—'}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500">
                      <div>IP: <span className="font-mono text-slate-700">{log.ip}</span></div>
                      {log.dispositivo_id && (
                        <div className="text-[10px] text-slate-400 truncate max-w-xs">
                          Dev: {log.dispositivo_id}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {log.exito ? (
                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Éxito
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-800">
                          <XCircle className="w-3.5 h-3.5 text-rose-600" /> Fallido
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-600 max-w-sm">
                      {log.detalle || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-500">
            <span>Total: <strong>{total}</strong> eventos</span>
            <div className="flex items-center gap-1">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-2.5 py-1 rounded bg-white border border-slate-300 disabled:opacity-40"
              >
                Anterior
              </button>
              <span className="px-2">Página {page} de {totalPages}</span>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="px-2.5 py-1 rounded bg-white border border-slate-300 disabled:opacity-40"
              >
                Siguiente
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
