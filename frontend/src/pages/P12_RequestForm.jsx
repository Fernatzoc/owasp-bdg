import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import api from '../api/client';
import Toast from '../components/Toast';
import {
  ClipboardList,
  Plus,
  Trash2,
  Calendar,
  Building2,
  Save,
  Send,
  ArrowLeft,
  AlertCircle
} from 'lucide-react';

export default function P12_RequestForm() {
  const navigate = useNavigate();
  const { id } = useParams(); // Si existe, es modo edición de borrador
  const isEditing = Boolean(id);

  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Formulario
  const [proveedorId, setProveedorId] = useState('');
  const [fechaEntrega, setFechaEntrega] = useState('');
  const [observaciones, setObservaciones] = useState('');
  const [lineas, setLineas] = useState([]);

  // Estado del submit
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState(null);

  const todayStr = new Date().toISOString().split('T')[0];

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [suppRes, prodRes] = await Promise.all([
        api.get('/suppliers?size=100&activo=true'),
        api.get('/products?size=200&activo=true')
      ]);
      setSuppliers(suppRes.data.items || []);
      setProducts(prodRes.data.items || []);

      if (isEditing) {
        const reqRes = await api.get(`/requests/${id}`);
        const r = reqRes.data;
        if (r.estado !== 'Borrador') {
          setToast({ type: 'error', message: 'Solo se pueden editar solicitudes en estado Borrador' });
          navigate('/solicitudes');
          return;
        }
        setProveedorId(r.proveedor_id);
        setFechaEntrega(r.fecha_entrega);
        setObservaciones(r.observaciones || '');
        setLineas(r.lineas.map((l) => ({
          producto_id: l.producto_id,
          cant_solicitada: l.cant_solicitada
        })));
      } else {
        // Inicializar con una línea vacía
        setLineas([{ producto_id: '', cant_solicitada: 1 }]);
      }
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando datos del formulario' });
    } finally {
      setLoading(false);
    }
  };

  const handleAddLine = () => {
    setLineas([...lineas, { producto_id: '', cant_solicitada: 1 }]);
  };

  const handleRemoveLine = (index) => {
    if (lineas.length === 1) {
      setToast({ type: 'warning', message: 'La solicitud debe tener al menos una línea' });
      return;
    }
    setLineas(lineas.filter((_, idx) => idx !== index));
  };

  const handleLineChange = (index, field, value) => {
    const updated = [...lineas];
    updated[index][field] = value;
    setLineas(updated);
  };

  const handleSubmit = async (enviarAlProveedor) => {
    if (!proveedorId) {
      setToast({ type: 'error', message: 'Por favor seleccione un proveedor' });
      return;
    }
    if (!fechaEntrega) {
      setToast({ type: 'error', message: 'Por favor indique la fecha requerida de entrega' });
      return;
    }
    if (fechaEntrega < todayStr) {
      setToast({ type: 'error', message: 'La fecha de entrega no puede ser anterior al día de hoy' });
      return;
    }

    // Validar productos y cantidades
    const seenProducts = new Set();
    for (const [idx, l] of lineas.entries()) {
      if (!l.producto_id) {
        setToast({ type: 'error', message: `Seleccione un producto en la línea ${idx + 1}` });
        return;
      }
      if (seenProducts.has(l.producto_id)) {
        setToast({ type: 'error', message: 'No se permite repetir productos en la misma solicitud' });
        return;
      }
      seenProducts.add(l.producto_id);

      const qty = parseFloat(l.cant_solicitada);
      if (isNaN(qty) || qty <= 0) {
        setToast({ type: 'error', message: `La cantidad solicitada en la línea ${idx + 1} debe ser mayor a 0` });
        return;
      }
    }

    setSubmitting(true);
    try {
      const payload = {
        proveedor_id: proveedorId,
        fecha_entrega: fechaEntrega,
        observaciones,
        lineas: lineas.map((l) => ({
          producto_id: l.producto_id,
          cant_solicitada: parseFloat(l.cant_solicitada)
        })),
        enviar: enviarAlProveedor
      };

      if (isEditing) {
        await api.patch(`/requests/${id}`, payload);
        if (enviarAlProveedor) {
          await api.post(`/requests/${id}/send`);
        }
      } else {
        await api.post('/requests', payload);
      }

      setToast({
        type: 'success',
        message: enviarAlProveedor
          ? 'Solicitud enviada al proveedor exitosamente'
          : 'Solicitud guardada como borrador'
      });

      setTimeout(() => {
        navigate('/solicitudes');
      }, 1000);
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al guardar solicitud' });
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
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            {isEditing ? 'Editar Borrador de Solicitud' : 'Nueva Solicitud de Compra'}
          </h1>
          <p className="mt-0.5 text-sm text-slate-500">
            Defina el proveedor, fecha de entrega y lista de productos requeridos
          </p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        {/* Cabecera de la solicitud */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-emerald-600" />
              Proveedor Activo <span className="text-rose-500">*</span>
            </label>
            <select
              value={proveedorId}
              onChange={(e) => setProveedorId(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            >
              <option value="">Seleccione un proveedor...</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.codigo} - {s.nombre}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-1 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-emerald-600" />
              Fecha de Entrega Requerida <span className="text-rose-500">*</span>
            </label>
            <input
              type="date"
              min={todayStr}
              value={fechaEntrega}
              onChange={(e) => setFechaEntrega(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-semibold text-slate-700 mb-1">
              Observaciones adicionales
            </label>
            <textarea
              rows={2}
              value={observaciones}
              onChange={(e) => setObservaciones(e.target.value)}
              placeholder="Instrucciones especiales de entrega, empaque o entrega en bodega..."
              className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        {/* Tabla de Líneas de Producto */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-bold text-slate-900">
              Líneas de Productos Solicitados ({lineas.length})
            </h3>
            <button
              type="button"
              onClick={handleAddLine}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 text-slate-700 text-xs font-bold rounded-lg hover:bg-slate-200 transition-colors"
            >
              <Plus className="w-4 h-4" /> Agregar Producto
            </button>
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
                <tr>
                  <th className="py-2.5 px-4 w-12 text-center">#</th>
                  <th className="py-2.5 px-4">Producto</th>
                  <th className="py-2.5 px-4 w-40">Cantidad Requerida</th>
                  <th className="py-2.5 px-4 w-16 text-center">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lineas.map((line, idx) => {
                  const selectedProd = products.find((p) => p.id === line.producto_id);

                  return (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 text-center font-bold text-slate-400">
                        {idx + 1}
                      </td>
                      <td className="py-3 px-4">
                        <select
                          value={line.producto_id}
                          onChange={(e) => handleLineChange(idx, 'producto_id', e.target.value)}
                          className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                        >
                          <option value="">Seleccione un producto...</option>
                          {products.map((p) => (
                            <option key={p.id} value={p.id}>
                              {p.codigo} - {p.nombre} ({p.unidad})
                            </option>
                          ))}
                        </select>
                        {selectedProd && (
                          <div className="text-xs text-slate-500 mt-1">
                            {selectedProd.descripcion || 'Sin descripción'} · Unidad: <strong>{selectedProd.unidad}</strong>
                          </div>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <input
                          type="number"
                          min="0.01"
                          step="any"
                          required
                          value={line.cant_solicitada}
                          onChange={(e) => handleLineChange(idx, 'cant_solicitada', e.target.value)}
                          className="w-full text-sm font-bold border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
                        />
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          type="button"
                          onClick={() => handleRemoveLine(idx)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                          title="Eliminar línea"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Acciones del formulario */}
        <div className="flex flex-col sm:flex-row items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Link
            to="/solicitudes"
            className="w-full sm:w-auto px-4 py-2.5 text-sm font-medium text-slate-700 bg-white border border-slate-300 rounded-xl hover:bg-slate-50 text-center"
          >
            Cancelar
          </Link>

          <button
            type="button"
            disabled={submitting}
            onClick={() => handleSubmit(false)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-800 text-white font-bold text-sm rounded-xl hover:bg-slate-900 shadow-sm disabled:opacity-50 transition-colors"
          >
            <Save className="w-4 h-4" />
            {submitting ? 'Guardando...' : 'Guardar como Borrador'}
          </button>

          <button
            type="button"
            disabled={submitting}
            onClick={() => handleSubmit(true)}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-emerald-600 text-white font-bold text-sm rounded-xl hover:bg-emerald-700 shadow-sm disabled:opacity-50 transition-colors"
          >
            <Send className="w-4 h-4" />
            {submitting ? 'Enviando...' : 'Enviar al Proveedor'}
          </button>
        </div>
      </div>
    </div>
  );
}
