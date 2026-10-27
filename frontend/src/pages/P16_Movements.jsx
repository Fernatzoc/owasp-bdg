import React, { useState, useEffect } from 'react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import Toast from '../components/Toast';
import {
  ArrowLeftRight,
  ClipboardList,
  Boxes,
  History,
  Search,
  Calendar,
  Building2,
  Package,
  ChevronDown,
  ChevronUp,
  Clock,
  User
} from 'lucide-react';

export default function P16_Movements() {
  const { isProveedor } = useAuth();

  // Pestañas: 'pedidos' | 'ingresos' | 'cambios'
  const [activeTab, setActiveTab] = useState('pedidos');

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Filtros comunes
  const [fechaDesde, setFechaDesde] = useState('');
  const [fechaHasta, setFechaHasta] = useState('');
  const [proveedorId, setProveedorId] = useState('');
  const [productoId, setProductoId] = useState('');
  const [numeroSolicitud, setNumeroSolicitud] = useState('');

  // Catálogos para los selects de filtro
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);

  // Estado para expandir detalle en pestaña 1
  const [expandedRequestId, setExpandedRequestId] = useState(null);

  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadFilterCatalogs();
  }, []);

  useEffect(() => {
    fetchMovements();
  }, [activeTab, proveedorId, productoId]);

  const loadFilterCatalogs = async () => {
    try {
      const [suppRes, prodRes] = await Promise.all([
        !isProveedor ? api.get('/suppliers?size=100') : Promise.resolve({ data: { items: [] } }),
        api.get('/products?size=200')
      ]);
      setSuppliers(suppRes.data.items || []);
      setProducts(prodRes.data.items || []);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchMovements = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('tipo', activeTab);
      if (fechaDesde) params.append('fecha_desde', fechaDesde);
      if (fechaHasta) params.append('fecha_hasta', fechaHasta);
      if (proveedorId) params.append('proveedor_id', proveedorId);
      if (productoId) params.append('producto_id', productoId);
      if (numeroSolicitud) params.append('numero_solicitud', numeroSolicitud);
      params.append('size', '50');

      const res = await api.get(`/movements?${params.toString()}`);
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando movimientos' });
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setExpandedRequestId(null);
  };

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
          <ArrowLeftRight className="w-7 h-7 text-emerald-600" />
          Consulta de Movimientos
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Trazabilidad y auditoría completa de pedidos, ingresos a inventario e histórico de estados
        </p>
      </div>

      {/* Pestañas en el orden estricto de la especificación */}
      <div className="flex border-b border-slate-200 bg-white px-2 pt-2 rounded-t-2xl shadow-sm">
        <button
          onClick={() => handleTabChange('pedidos')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'pedidos'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ClipboardList className="w-4 h-4" />
          1. Pedidos
        </button>

        <button
          onClick={() => handleTabChange('ingresos')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'ingresos'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Boxes className="w-4 h-4" />
          2. Productos Ingresados
        </button>

        <button
          onClick={() => handleTabChange('cambios')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all ${
            activeTab === 'cambios'
              ? 'border-emerald-600 text-emerald-700 bg-emerald-50/50 rounded-t-lg'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <History className="w-4 h-4" />
          3. Cambios (Línea de Tiempo)
        </button>
      </div>

      {/* Barra de Filtros Comunes */}
      <div className="bg-white p-4 rounded-b-2xl -mt-6 border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        <div>
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Número Solicitud</label>
          <input
            type="text"
            placeholder="SOL-2026-..."
            value={numeroSolicitud}
            onChange={(e) => setNumeroSolicitud(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        {!isProveedor && (
          <div>
            <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Proveedor</label>
            <select
              value={proveedorId}
              onChange={(e) => setProveedorId(e.target.value)}
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
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Producto</label>
          <select
            value={productoId}
            onChange={(e) => setProductoId(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="">Todos los productos</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.codigo} - {p.nombre}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-bold uppercase text-slate-500 mb-1">Rango Desde</label>
          <input
            type="date"
            value={fechaDesde}
            onChange={(e) => setFechaDesde(e.target.value)}
            className="w-full text-sm border border-slate-300 rounded-lg p-2 outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <div className="flex items-end">
          <button
            onClick={fetchMovements}
            className="w-full py-2 bg-slate-800 text-white font-bold text-sm rounded-lg hover:bg-slate-900 shadow-sm transition-colors"
          >
            Filtrar Resultados
          </button>
        </div>
      </div>

      {/* Contenido según pestaña activa */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="py-16 text-center text-slate-400">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600 mx-auto mb-2"></div>
            Cargando registros...
          </div>
        ) : items.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            No se encontraron movimientos con los filtros especificados
          </div>
        ) : (
          <>
            {/* PESTAÑA 1: PEDIDOS */}
            {activeTab === 'pedidos' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
                    <tr>
                      <th className="py-3 px-4">Número</th>
                      <th className="py-3 px-4">Proveedor</th>
                      <th className="py-3 px-4">Fecha Creación</th>
                      <th className="py-3 px-4">Fecha Entrega Requerida</th>
                      <th className="py-3 px-4">Estado Actual</th>
                      <th className="py-3 px-4 text-center">Total Líneas</th>
                      <th className="py-3 px-4 text-center">Detalle</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((r) => {
                      const isExpanded = expandedRequestId === r.solicitud_id;

                      return (
                        <React.Fragment key={r.solicitud_id}>
                          <tr className="hover:bg-slate-50/70 transition-colors">
                            <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                              {r.numero}
                            </td>
                            <td className="py-3.5 px-4 font-medium text-slate-800">
                              {r.proveedor}
                            </td>
                            <td className="py-3.5 px-4 text-xs text-slate-500">
                              {r.fecha_creacion ? new Date(r.fecha_creacion).toLocaleDateString('es-GT') : '—'}
                            </td>
                            <td className="py-3.5 px-4 text-xs font-bold text-slate-700">
                              {r.fecha_entrega}
                            </td>
                            <td className="py-3.5 px-4">
                              <StatusBadge status={r.estado} size="small" />
                            </td>
                            <td className="py-3.5 px-4 text-center font-bold text-slate-800">
                              {r.total_lineas}
                            </td>
                            <td className="py-3.5 px-4 text-center">
                              <button
                                onClick={() => setExpandedRequestId(isExpanded ? null : r.solicitud_id)}
                                className="inline-flex items-center gap-1 text-xs font-bold text-emerald-600 hover:text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg"
                              >
                                {isExpanded ? 'Ocultar' : 'Ver Líneas'}
                                {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                              </button>
                            </td>
                          </tr>

                          {/* Detalle expandido de líneas */}
                          {isExpanded && (
                            <tr className="bg-slate-50/90">
                              <td colSpan={7} className="p-4">
                                <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500 mb-2">
                                    Detalle de Líneas de la Solicitud
                                  </h4>
                                  <table className="w-full text-xs text-left">
                                    <thead className="bg-slate-100 text-slate-600 uppercase font-bold">
                                      <tr>
                                        <th className="p-2">Código</th>
                                        <th className="p-2">Producto</th>
                                        <th className="p-2 text-center">Solicitado</th>
                                        <th className="p-2 text-center">Confirmado</th>
                                        <th className="p-2 text-center">Recibido</th>
                                        <th className="p-2">Motivo</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                      {r.lineas?.map((line, idx) => (
                                        <tr key={idx}>
                                          <td className="p-2 font-mono font-bold text-slate-700">{line.codigo}</td>
                                          <td className="p-2 font-semibold text-slate-900">{line.nombre}</td>
                                          <td className="p-2 text-center font-bold text-slate-800">{line.cant_solicitada}</td>
                                          <td className="p-2 text-center font-bold text-blue-700">{line.cant_confirmada}</td>
                                          <td className="p-2 text-center font-black text-emerald-700">{line.cant_recibida}</td>
                                          <td className="p-2 text-slate-500 italic">{line.motivo || '—'}</td>
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}

            {/* PESTAÑA 2: PRODUCTOS INGRESADOS */}
            {activeTab === 'ingresos' && (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase text-slate-500">
                    <tr>
                      <th className="py-3 px-4">Fecha de Recepción</th>
                      <th className="py-3 px-4">No. Solicitud</th>
                      <th className="py-3 px-4">Código Producto</th>
                      <th className="py-3 px-4">Nombre de Producto</th>
                      <th className="py-3 px-4 text-right">Cantidad Recibida</th>
                      <th className="py-3 px-4">Usuario que Recibió</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {items.map((ing) => (
                      <tr key={ing.id} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3.5 px-4 text-xs text-slate-600 font-medium">
                          {new Date(ing.fecha_recepcion).toLocaleString('es-GT')}
                        </td>
                        <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                          {ing.numero_solicitud}
                        </td>
                        <td className="py-3.5 px-4 font-mono text-xs font-semibold text-slate-700">
                          {ing.codigo_producto}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-slate-800">
                          {ing.nombre_producto}
                        </td>
                        <td className="py-3.5 px-4 text-right font-black text-emerald-700">
                          +{ing.cantidad_recibida}
                        </td>
                        <td className="py-3.5 px-4 text-xs font-medium text-slate-700">
                          <span className="inline-flex items-center gap-1.5 bg-slate-100 px-2.5 py-1 rounded-full">
                            <User className="w-3 h-3 text-slate-500" />
                            {ing.usuario_recibio}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* PESTAÑA 3: CAMBIOS (LÍNEA DE TIEMPO) */}
            {activeTab === 'cambios' && (
              <div className="p-6">
                <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
                  {items.map((c) => (
                    <div key={c.id} className="relative group">
                      {/* Punto en la línea de tiempo */}
                      <div className="absolute -left-6 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-emerald-600 flex items-center justify-center shadow-sm">
                        <div className="w-2 h-2 rounded-full bg-emerald-600"></div>
                      </div>

                      <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-emerald-300 transition-colors">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold text-slate-900 bg-white px-2 py-0.5 rounded border border-slate-200">
                              {c.numero_solicitud}
                            </span>
                            <span className="font-bold text-emerald-800 uppercase text-[10px] tracking-wider">
                              {c.tipo_movimiento}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5 text-slate-400">
                            <Clock className="w-3.5 h-3.5" />
                            {new Date(c.fecha_hora).toLocaleString('es-GT')}
                          </div>
                        </div>

                        {c.estado_anterior || c.estado_nuevo ? (
                          <div className="flex items-center gap-2 text-xs font-medium text-slate-700 mt-2">
                            <span>Estado:</span>
                            {c.estado_anterior && <StatusBadge status={c.estado_anterior} size="small" />}
                            <span className="text-slate-400 font-bold">→</span>
                            {c.estado_nuevo && <StatusBadge status={c.estado_nuevo} size="small" />}
                          </div>
                        ) : null}

                        {c.comentario && (
                          <div className="text-xs text-slate-600 mt-2 bg-white p-2.5 rounded-lg border border-slate-100">
                            <strong>Comentario:</strong> {c.comentario}
                          </div>
                        )}

                        <div className="mt-2 text-[11px] text-slate-400">
                          Registrado por: <strong className="text-slate-600">{c.usuario}</strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
