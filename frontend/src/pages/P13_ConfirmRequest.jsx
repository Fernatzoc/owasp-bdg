import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/StatusBadge';
import Toast from '../components/Toast';
import {
  CheckCircle,
  XCircle,
  ArrowLeft,
  Calendar,
  AlertTriangle,
  Send,
  MessageSquare
} from 'lucide-react';

export default function P13_ConfirmRequest() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);

  // Cantidades confirmadas por producto: { [productId]: number }
  const [confirmedQtys, setConfirmedQtys] = useState({});
  const [nuevaFecha, setNuevaFecha] = useState('');
  const [comentario, setComentario] = useState('');

  // Modal Rechazar
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [motivoRechazo, setMotivoRechazo] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchRequestDetail();
  }, [id]);

  const fetchRequestDetail = async () => {
    setLoading(true);
    try {
      const res = await api.get(`/requests/${id}`);
      const r = res.data;
      if (r.estado !== 'Enviada') {
        setToast({ type: 'warning', message: `La solicitud está en estado '${r.estado}', no se puede confirmar` });
      }
      setRequest(r);
      // Inicializar cantidades con lo solicitado por defecto
      const initialQtys = {};
      r.lineas.forEach((l) => {
        initialQtys[l.producto_id] = l.cant_confirmada > 0 ? l.cant_confirmada : l.cant_solicitada;
      });
      setConfirmedQtys(initialQtys);
      setNuevaFecha(r.fecha_entrega);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando la solicitud' });
    } finally {
      setLoading(false);
    }
  };

  const handleQtyChange = (productId, val, maxQty) => {
    const num = parseFloat(val);
    if (isNaN(num)) {
      setConfirmedQtys({ ...confirmedQtys, [productId]: '' });
      return;
    }
    const clamped = Math.max(0, Math.min(num, maxQty));
    setConfirmedQtys({ ...confirmedQtys, [productId]: clamped });
  };

  const isPartialConfirmation = () => {
    if (!request) return false;
    return request.lineas.some((l) => (parseFloat(confirmedQtys[l.producto_id]) || 0) < l.cant_solicitada);
  };

  const handleConfirmSubmit = async () => {
    setSubmitting(true);
    try {
      const payloadLines = request.lineas.map((l) => ({
        producto_id: l.producto_id,
        cant_confirmada: parseFloat(confirmedQtys[l.producto_id]) || 0
      }));

      await api.post(`/requests/${id}/confirm`, {
        lineas: payloadLines,
        nueva_fecha_entrega: nuevaFecha !== request.fecha_entrega ? nuevaFecha : null,
        comentario: comentario.trim() || null
      });

      setToast({ type: 'success', message: 'Solicitud confirmada exitosamente. Estado: Por entregar' });
      setTimeout(() => navigate('/solicitudes'), 1000);
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al confirmar solicitud' });
      setSubmitting(false);
    }
  };

  const handleRejectSubmit = async (e) => {
    e.preventDefault();
    if (!motivoRechazo.trim()) {
      setToast({ type: 'error', message: 'Debe ingresar un motivo de rechazo' });
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/requests/${id}/reject`, { motivo: motivoRechazo });
      setToast({ type: 'success', message: 'Solicitud rechazada' });
      setTimeout(() => navigate('/solicitudes'), 1000);
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al rechazar solicitud' });
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (!request) return null;

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div className="flex items-center gap-3">
        <Link
          to="/solicitudes"
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              Confirmación de Solicitud {request.numero}
            </h1>
            <StatusBadge status={request.estado} />
          </div>
          <p className="mt-0.5 text-sm text-slate-500">
            Revise los productos solicitados e indique las cantidades disponibles para despacho
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        {/* Encabezado */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200 text-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Proveedor:</span>
            <div className="font-semibold text-slate-900 mt-0.5">{request.nombre_proveedor}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Fecha de Entrega Requerida:</span>
            <div className="font-semibold text-slate-900 mt-0.5">{request.fecha_entrega}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Observaciones de Compras:</span>
            <div className="text-slate-700 mt-0.5">{request.observaciones || 'Sin observaciones'}</div>
          </div>
        </div>

        {/* Alerta de confirmación parcial */}
        {isPartialConfirmation() && (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-sm flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <div className="font-bold">Aviso de Confirmación Parcial</div>
              <p className="text-xs text-amber-800 mt-0.5">
                Está confirmando una cantidad menor a la solicitada en una o más líneas. El sistema notificará a Compras y registrará la entrega como parcial.
              </p>
            </div>
          </div>
        )}

        {/* Tabla de Productos para Confirmar */}
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
              <tr>
                <th className="py-3 px-4">Código</th>
                <th className="py-3 px-4">Producto</th>
                <th className="py-3 px-4 text-center">Cant. Solicitada</th>
                <th className="py-3 px-4 w-44 text-center bg-emerald-50/50">
                  Puede Entregar <span className="text-rose-500">*</span>
                </th>
                <th className="py-3 px-4 text-center">Estado Línea</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {request.lineas.map((line) => {
                const confirmed = parseFloat(confirmedQtys[line.producto_id]) || 0;
                const isShortage = confirmed < line.cant_solicitada;

                return (
                  <tr key={line.producto_id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-700">
                      {line.codigo}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      {line.nombre}
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-slate-800">
                      {line.cant_solicitada}
                    </td>
                    <td className="py-3.5 px-4 bg-emerald-50/20">
                      <input
                        type="number"
                        min="0"
                        max={line.cant_solicitada}
                        step="any"
                        value={confirmedQtys[line.producto_id] ?? ''}
                        onChange={(e) =>
                          handleQtyChange(line.producto_id, e.target.value, line.cant_solicitada)
                        }
                        className="w-full text-center text-sm font-black border border-emerald-300 rounded-lg py-1.5 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-emerald-900"
                      />
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      {confirmed === line.cant_solicitada ? (
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                          Completo
                        </span>
                      ) : (
                        <span className="text-xs font-bold text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
                          Parcial ({confirmed}/{line.cant_solicitada})
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Ajustes opcionales de fecha y comentario */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-emerald-600" />
              Nueva Fecha Estimada de Entrega (Opcional):
            </label>
            <input
              type="date"
              value={nuevaFecha}
              onChange={(e) => setNuevaFecha(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <MessageSquare className="w-4 h-4 text-emerald-600" />
              Comentarios del Proveedor:
            </label>
            <input
              type="text"
              value={comentario}
              onChange={(e) => setComentario(e.target.value)}
              placeholder="Ej. Despacho programado para las 9:00 AM..."
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Botones Confirmar / Rechazar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-4 border-t border-slate-100">
          <button
            type="button"
            disabled={submitting}
            onClick={() => setRejectModalOpen(true)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-rose-50 text-rose-700 border border-rose-200 font-bold text-sm rounded-xl hover:bg-rose-100 transition-colors"
          >
            <XCircle className="w-4 h-4 text-rose-600" />
            Rechazar Solicitud Completa
          </button>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <Link
              to="/solicitudes"
              className="w-full sm:w-auto px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 text-center"
            >
              Regresar
            </Link>

            <button
              type="button"
              disabled={submitting}
              onClick={handleConfirmSubmit}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-emerald-600 text-white font-bold text-sm rounded-xl hover:bg-emerald-700 shadow-sm transition-colors"
            >
              <CheckCircle className="w-4 h-4" />
              {submitting ? 'Confirmando...' : 'Confirmar Cantidades a Entregar'}
            </button>
          </div>
        </div>
      </div>

      {/* Modal Rechazar Solicitud */}
      {rejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-lg">Rechazar Solicitud de Compra</h3>
              <button onClick={() => setRejectModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                &times;
              </button>
            </div>
            <form onSubmit={handleRejectSubmit} className="p-6 space-y-4">
              <p className="text-xs text-slate-600">
                Indique el motivo por el cual no es posible atender esta orden (falta de existencias, capacidad operativa, etc.).
              </p>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Motivo de rechazo <span className="text-rose-500">*</span>
                </label>
                <textarea
                  required
                  rows={3}
                  value={motivoRechazo}
                  onChange={(e) => setMotivoRechazo(e.target.value)}
                  placeholder="Explique el motivo..."
                  className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setRejectModalOpen(false)}
                  className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-rose-600 text-white font-bold text-sm rounded-lg hover:bg-rose-700 shadow-sm"
                >
                  {submitting ? 'Rechazando...' : 'Confirmar Rechazo'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
