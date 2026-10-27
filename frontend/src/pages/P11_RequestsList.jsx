import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import ConfirmModal from '../components/ConfirmModal';
import Toast from '../components/Toast';
import {
  ClipboardList,
  Search,
  PlusCircle,
  Eye,
  Edit,
  Send,
  XCircle,
  CheckCircle,
  PackageCheck,
  Calendar,
  AlertCircle
} from 'lucide-react';

export default function P11_RequestsList() {
  const { isCompras, isProveedor, isBodega, isAdmin, user } = useAuth();

  const [requests, setRequests] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filtros
  const [searchNumero, setSearchNumero] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [supplierFilter, setSupplierFilter] = useState('');
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');

  // Modales
  const [cancelModalReq, setCancelModalReq] = useState(null);
  const [cancelMotivo, setCancelMotivo] = useState('');
  const [modalLoading, setModalLoading] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchRequests();
    if (!isProveedor) {
      fetchSuppliers();
    }
  }, [statusFilter, supplierFilter]);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchNumero) params.append('numero', searchNumero);
      if (statusFilter) params.append('estado', statusFilter);
      if (supplierFilter) params.append('proveedor_id', supplierFilter);
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);

      const res = await api.get(`/requests?${params.toString()}`);
      setRequests(res.data.items || []);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando solicitudes' });
    } finally {
      setLoading(false);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const res = await api.get('/suppliers?size=100');
      setSuppliers(res.data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendRequest = async (reqId) => {
    try {
      await api.post(`/requests/${reqId}/send`);
      setToast({ type: 'success', message: 'Solicitud enviada al proveedor exitosamente' });
      fetchRequests();
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al enviar solicitud' });
    }
  };

  const handleCancelSubmit = async (e) => {
    e.preventDefault();
    if (!cancelMotivo.trim()) {
      setToast({ type: 'error', message: 'Debe ingresar el motivo de cancelación' });
      return;
    }

    setModalLoading(true);
    try {
      await api.post(`/requests/${cancelModalReq.id}/cancel`, { motivo: cancelMotivo });
      setToast({ type: 'success', message: 'Solicitud cancelada exitosamente' });
      setCancelModalReq(null);
      setCancelMotivo('');
      fetchRequests();
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al cancelar solicitud' });
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <ClipboardList className="w-7 h-7 text-emerald-600" />
            Solicitudes a Proveedores
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Gestione el ciclo de vida completo de pedidos desde la cotización hasta la recepción
          </p>
        </div>

        {(isCompras || isAdmin) && (
          <Link
            to="/solicitudes/nueva"
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white font-bold text-sm rounded-xl hover:bg-emerald-700 shadow-sm transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Nueva Solicitud
          </Link>
        )}
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div>
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Buscar por Número</label>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="SOL-2026-..."
              value={searchNumero}
              onChange={(e) => setSearchNumero(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Estado</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Todos los estados</option>
            <option value="Borrador">Borrador</option>
            <option value="Enviada">Enviada</option>
            <option value="Por entregar">Por entregar</option>
            <option value="Entregada">Entregada</option>
            <option value="Entregada parcial">Entregada parcial</option>
            <option value="Cerrada con faltante">Cerrada con faltante</option>
            <option value="Rechazada">Rechazada</option>
            <option value="Cancelada">Cancelada</option>
          </select>
        </div>

        {!isProveedor && (
          <div>
            <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Proveedor</label>
            <select
              value={supplierFilter}
              onChange={(e) => setSupplierFilter(e.target.value)}
              className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="">Todos los proveedores</option>
              {suppliers.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.codigo} - {s.nombre}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Fecha Entrega Desde</label>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={fetchRequests}
            className="w-full py-2 bg-slate-800 text-white font-bold text-sm rounded-lg hover:bg-slate-900 shadow-sm"
          >
            Aplicar Filtros
          </button>
        </div>
      </div>

      {/* Tabla de Solicitudes */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Número</th>
                <th className="py-3 px-4">Proveedor</th>
                <th className="py-3 px-4">Fecha Entrega</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4 text-center">Líneas</th>
                <th className="py-3 px-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    Cargando solicitudes...
                  </td>
                </tr>
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-400">
                    No se encontraron solicitudes
                  </td>
                </tr>
              ) : (
                requests.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      {r.numero}
                    </td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">
                      {r.nombre_proveedor}
                    </td>
                    <td className="py-3.5 px-4 text-xs font-semibold text-slate-600">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        {r.fecha_entrega}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={r.estado} />
                      {r.es_confirmacion_parcial && (
                        <span className="block text-[10px] text-amber-700 font-bold mt-0.5">
                          ⚠️ Parcial
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700">
                        {r.total_lineas}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {/* Ver detalle / Confirmar según rol */}
                        {(isProveedor || isAdmin) && r.estado === 'Enviada' && (
                          <Link
                            to={`/solicitudes/${r.id}/confirmar`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-amber-600 text-white text-xs font-bold rounded-lg hover:bg-amber-700 shadow-sm"
                            title="Confirmar cantidades a entregar"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            Confirmar
                          </Link>
                        )}

                        {/* Recepción para Bodega */}
                        {(isBodega || isAdmin) && (r.estado === 'Por entregar' || r.estado === 'Entregada parcial') && (
                          <Link
                            to={`/solicitudes/${r.id}/recibir`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-emerald-600 text-white text-xs font-bold rounded-lg hover:bg-emerald-700 shadow-sm"
                            title="Registrar recepción física e inventario"
                          >
                            <PackageCheck className="w-3.5 h-3.5" />
                            Recibir
                          </Link>
                        )}

                        {/* Enviar al proveedor (Compras) */}
                        {(isCompras || isAdmin) && r.estado === 'Borrador' && (
                          <button
                            onClick={() => handleSendRequest(r.id)}
                            className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 shadow-sm"
                            title="Enviar al proveedor"
                          >
                            <Send className="w-3.5 h-3.5" />
                            Enviar
                          </button>
                        )}

                        {/* Editar Borrador (Compras) */}
                        {(isCompras || isAdmin) && r.estado === 'Borrador' && (
                          <Link
                            to={`/solicitudes/${r.id}/editar`}
                            className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                            title="Editar borrador"
                          >
                            <Edit className="w-4 h-4" />
                          </Link>
                        )}

                        {/* Cancelar solicitud (Compras / Admin) */}
                        {(isCompras || isAdmin) && ['Borrador', 'Enviada'].includes(r.estado) && (
                          <button
                            onClick={() => {
                              setCancelModalReq(r);
                              setCancelMotivo('');
                            }}
                            className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                            title="Cancelar solicitud"
                          >
                            <XCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Cancelar Solicitud */}
      {cancelModalReq && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-lg">Cancelar Solicitud</h3>
              <button onClick={() => setCancelModalReq(null)} className="text-slate-400 hover:text-slate-600">
                &times;
              </button>
            </div>
            <form onSubmit={handleCancelSubmit} className="p-6 space-y-4">
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs">
                Se cancelará la solicitud <span className="font-bold">{cancelModalReq.numero}</span>. Esta acción no se puede revertir.
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-1">
                  Motivo de cancelación (obligatorio):
                </label>
                <textarea
                  required
                  rows={3}
                  value={cancelMotivo}
                  onChange={(e) => setCancelMotivo(e.target.value)}
                  placeholder="Explique la razón de la cancelación..."
                  className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-rose-500"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCancelModalReq(null)}
                  className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg"
                >
                  Regresar
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 bg-rose-600 text-white font-bold text-sm rounded-lg hover:bg-rose-700 shadow-sm"
                >
                  {modalLoading ? 'Cancelando...' : 'Confirmar Cancelación'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
