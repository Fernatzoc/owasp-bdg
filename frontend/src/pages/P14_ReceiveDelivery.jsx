import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../api/client';
import StatusBadge from '../components/StatusBadge';
import Toast from '../components/Toast';
import {
  PackageCheck,
  ArrowLeft,
  Boxes,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Truck
} from 'lucide-react';

const MOTIVOS_DISPONIBLES = [
  'faltante',
  'dañado',
  'producto incorrecto',
  'otro'
];

export default function P14_ReceiveDelivery() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);

  // Estado por línea: { [productId]: { recibido: bool, cant_recibida: number, motivo: string } }
  const [receiveData, setReceiveData] = useState({});
  const [comentarioGeneral, setComentarioGeneral] = useState('');

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
      if (!['Por entregar', 'Entregada parcial'].includes(r.estado)) {
        setToast({ type: 'warning', message: `Estado '${r.estado}' no admite recepción` });
      }
      setRequest(r);

      // Inicializar datos de recepción
      const initial = {};
      r.lineas.forEach((l) => {
        const pendiente = Math.max(0, l.cant_confirmada - l.cant_recibida);
        initial[l.producto_id] = {
          recibido: pendiente > 0,
          cant_recibida: pendiente,
          motivo: ''
        };
      });
      setReceiveData(initial);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando solicitud' });
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (productId, field, value) => {
    setReceiveData((prev) => ({
      ...prev,
      [productId]: {
        ...prev[productId],
        [field]: value
      }
    }));
  };

  // Calcular resumen de lo que entrará al inventario
  const inventorySummary = request?.lineas
    .map((l) => {
      const itemData = receiveData[l.producto_id] || {};
      const qtyIngresada = itemData.recibido ? parseFloat(itemData.cant_recibida) || 0 : 0;
      return {
        codigo: l.codigo,
        nombre: l.nombre,
        qty: qtyIngresada
      };
    })
    .filter((item) => item.qty > 0) || [];

  const handleReceiveSubmit = async () => {
    // Validar motivos si la cantidad ingresada es menor a lo pendiente por recibir
    for (const line of request.lineas) {
      const pId = line.producto_id;
      const data = receiveData[pId];
      const pendiente = Math.max(0, line.cant_confirmada - line.cant_recibida);
      const ingresada = data.recibido ? parseFloat(data.cant_recibida) || 0 : 0;

      if (ingresada < pendiente && !data.motivo) {
        setToast({
          type: 'error',
          message: `Debe indicar el motivo por el cual la entrega de '${line.nombre}' es menor a lo confirmado`
        });
        return;
      }
    }

    setSubmitting(true);
    try {
      const payloadLines = request.lineas.map((line) => {
        const data = receiveData[line.producto_id];
        return {
          producto_id: line.producto_id,
          recibido: Boolean(data.recibido),
          cant_recibida: data.recibido ? parseFloat(data.cant_recibida) || 0 : 0,
          motivo: data.motivo || null
        };
      });

      await api.post(`/requests/${id}/receive`, {
        lineas: payloadLines,
        comentario: comentarioGeneral.trim() || null
      });

      setToast({
        type: 'success',
        message: 'Recepción registrada y existencias sumadas al inventario satisfactoriamente'
      });

      setTimeout(() => navigate('/inventario'), 1200);
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al procesar la recepción' });
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
              Recepción de Entrega - {request.numero}
            </h1>
            <StatusBadge status={request.estado} />
          </div>
          <p className="mt-0.5 text-sm text-slate-500">
            Verifique la mercancía recibida en bodega y confirme el ingreso directo a inventario
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        {/* Cabecera */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-xl border border-slate-200 text-sm">
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Proveedor:</span>
            <div className="font-semibold text-slate-900 mt-0.5">{request.nombre_proveedor}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Fecha de Entrega:</span>
            <div className="font-semibold text-slate-900 mt-0.5">{request.fecha_entrega}</div>
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase">Estado Actual:</span>
            <div className="mt-0.5"><StatusBadge status={request.estado} size="small" /></div>
          </div>
        </div>

        {/* Tabla de Productos para Recepción */}
        <div className="border border-slate-200 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
              <tr>
                <th className="py-3 px-4">Producto</th>
                <th className="py-3 px-4 text-center">Solicitado</th>
                <th className="py-3 px-4 text-center">Confirmado</th>
                <th className="py-3 px-4 text-center">Ya Recibido</th>
                <th className="py-3 px-4 text-center">¿Recibido?</th>
                <th className="py-3 px-4 w-32 text-center bg-emerald-50/50">Cant. Recibida</th>
                <th className="py-3 px-4 w-48">Motivo si es menor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {request.lineas.map((line) => {
                const pId = line.producto_id;
                const lineState = receiveData[pId] || { recibido: false, cant_recibida: 0, motivo: '' };
                const maxPermitido = Math.max(0, line.cant_confirmada - line.cant_recibida);
                const isShortage = lineState.cant_recibida < maxPermitido;

                return (
                  <tr key={pId} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4">
                      <div className="font-mono text-xs font-bold text-slate-500">{line.codigo}</div>
                      <div className="font-semibold text-slate-900">{line.nombre}</div>
                    </td>
                    <td className="py-3.5 px-4 text-center font-medium text-slate-600">
                      {line.cant_solicitada}
                    </td>
                    <td className="py-3.5 px-4 text-center font-bold text-slate-900">
                      {line.cant_confirmada}
                    </td>
                    <td className="py-3.5 px-4 text-center font-medium text-slate-600">
                      {line.cant_recibida}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <input
                        type="checkbox"
                        checked={lineState.recibido}
                        onChange={(e) => handleFieldChange(pId, 'recibido', e.target.checked)}
                        className="rounded text-emerald-600 focus:ring-emerald-500 w-5 h-5 cursor-pointer"
                      />
                    </td>
                    <td className="py-3.5 px-4 bg-emerald-50/20">
                      <input
                        type="number"
                        min="0"
                        max={maxPermitido}
                        step="any"
                        disabled={!lineState.recibido}
                        value={lineState.cant_recibida}
                        onChange={(e) => handleFieldChange(pId, 'cant_recibida', e.target.value)}
                        className="w-full text-center text-sm font-black border border-emerald-300 rounded-lg py-1.5 focus:ring-2 focus:ring-emerald-500 outline-none bg-white text-emerald-900 disabled:bg-slate-100 disabled:text-slate-400"
                      />
                    </td>
                    <td className="py-3.5 px-4">
                      {isShortage && (
                        <select
                          value={lineState.motivo}
                          onChange={(e) => handleFieldChange(pId, 'motivo', e.target.value)}
                          className="w-full text-xs border border-amber-300 rounded-lg p-1.5 bg-amber-50/50 text-amber-900 outline-none focus:ring-2 focus:ring-amber-500"
                        >
                          <option value="">Seleccione motivo...</option>
                          {MOTIVOS_DISPONIBLES.map((m) => (
                            <option key={m} value={m}>{m}</option>
                          ))}
                        </select>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Resumen de lo que entrará al inventario */}
        <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2">
          <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
            <Boxes className="w-4 h-4 text-emerald-700" />
            Resumen: Ingreso Atómico al Inventario
          </div>
          {inventorySummary.length === 0 ? (
            <p className="text-xs text-emerald-700 italic">
              No se ha marcado ninguna cantidad para ingresar al inventario.
            </p>
          ) : (
            <ul className="text-xs text-emerald-800 space-y-1">
              {inventorySummary.map((item, idx) => (
                <li key={idx} className="flex items-center justify-between">
                  <span>
                    • <span className="font-semibold">{item.nombre}</span> ({item.codigo})
                  </span>
                  <span className="font-black text-emerald-900">
                    +{item.qty} unidades
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-700 mb-1">
            Comentario o notas de recepción en bodega (opcional):
          </label>
          <input
            type="text"
            value={comentarioGeneral}
            onChange={(e) => setComentarioGeneral(e.target.value)}
            placeholder="Ej. Recibido en andén 2, empaques sellados..."
            className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {/* Botones */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Link
            to="/solicitudes"
            className="px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50"
          >
            Cancelar
          </Link>

          <button
            type="button"
            disabled={submitting || inventorySummary.length === 0}
            onClick={handleReceiveSubmit}
            className="inline-flex items-center gap-2 px-6 py-2.5 bg-emerald-600 text-white font-bold text-sm rounded-xl hover:bg-emerald-700 shadow-sm disabled:opacity-50 transition-colors"
          >
            <PackageCheck className="w-4 h-4" />
            {submitting ? 'Registrando en Inventario...' : 'Confirmar Recepción de Entrega'}
          </button>
        </div>
      </div>
    </div>
  );
}
