import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import StatusBadge from '../components/StatusBadge';
import {
  ClipboardList,
  Calendar,
  AlertTriangle,
  Boxes,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  PackageCheck
} from 'lucide-react';

export default function P07_Dashboard() {
  const { user, isCompras, isAdmin, isProveedor } = useAuth();

  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [stateCounts, setStateCounts] = useState({});
  const [upcomingDeliveries, setUpcomingDeliveries] = useState([]);
  const [lowStockProducts, setLowStockProducts] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Obtener solicitudes
      const reqRes = await api.get('/requests?size=100');
      const allRequests = reqRes.data.items || [];
      setRequests(allRequests);

      // Conteo por estado
      const counts = {};
      allRequests.forEach((r) => {
        counts[r.estado] = (counts[r.estado] || 0) + 1;
      });
      setStateCounts(counts);

      // Entregas próximas en los próximos 7 días
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const nextWeek = new Date(today);
      nextWeek.setDate(nextWeek.getDate() + 7);

      const upcoming = allRequests.filter((r) => {
        if (!r.fecha_entrega || ['Entregada', 'Cancelada', 'Rechazada'].includes(r.estado)) {
          return false;
        }
        const delivDate = new Date(r.fecha_entrega);
        return delivDate >= today && delivDate <= nextWeek;
      });
      setUpcomingDeliveries(upcoming);

      // 2. Obtener inventario para alerta de stock bajo
      const invRes = await api.get('/inventory?size=100');
      const allInventory = invRes.data.items || [];
      setInventory(allInventory);

      // Considerar stock bajo productos con cantidad < 50
      const lowStock = allInventory.filter((item) => item.cantidad < 50);
      setLowStockProducts(lowStock);
    } catch (err) {
      console.error('Error cargando métricas del dashboard:', err);
    } finally {
      setLoading(false);
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
      {/* Bienvenida y Acciones Rápidas */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            ¡Hola, {user?.nombre || 'Usuario'}!
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Resumen operativo y estado actual del inventario y pedidos.
          </p>
        </div>

        {(isCompras || isAdmin) && (
          <Link
            to="/solicitudes/nueva"
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-emerald-600 text-white font-bold text-sm shadow hover:bg-emerald-700 transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Nueva Solicitud de Compra
          </Link>
        )}
      </div>

      {/* Tarjetas de Solicitudes por Estado */}
      <div>
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">
          Solicitudes por Estado
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {[
            { label: 'Borrador', count: stateCounts['Borrador'] || 0, color: 'text-slate-700', bg: 'bg-slate-50' },
            { label: 'Enviada', count: stateCounts['Enviada'] || 0, color: 'text-blue-700', bg: 'bg-blue-50/60' },
            { label: 'Por entregar', count: stateCounts['Por entregar'] || 0, color: 'text-amber-800', bg: 'bg-amber-50/60' },
            { label: 'Entregada', count: stateCounts['Entregada'] || 0, color: 'text-emerald-700', bg: 'bg-emerald-50/60' },
            { label: 'Entregada parcial', count: stateCounts['Entregada parcial'] || 0, color: 'text-orange-800', bg: 'bg-orange-50/60' },
            { label: 'Cerrada / Cancelada', count: (stateCounts['Cerrada con faltante'] || 0) + (stateCounts['Cancelada'] || 0) + (stateCounts['Rechazada'] || 0), color: 'text-rose-700', bg: 'bg-rose-50/60' },
          ].map((item, idx) => (
            <div key={idx} className={`p-4 rounded-xl border border-slate-200 ${item.bg}`}>
              <div className="text-xs font-semibold text-slate-500">{item.label}</div>
              <div className={`text-2xl font-black mt-1 ${item.color}`}>{item.count}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Tarjeta: Entregas Próximas (7 días) */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-600" />
              <h3 className="font-bold text-slate-900 text-base">Entregas Próximas (7 Días)</h3>
            </div>
            <Link to="/solicitudes" className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1">
              Ver todas <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="mt-4 flex-1 space-y-3">
            {upcomingDeliveries.length === 0 ? (
              <div className="py-8 text-center text-sm text-slate-400">
                No hay entregas programadas en los próximos 7 días
              </div>
            ) : (
              upcomingDeliveries.map((req) => (
                <div
                  key={req.id}
                  className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between hover:bg-slate-100/60 transition-colors"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-800 text-sm">{req.numero}</span>
                      <StatusBadge status={req.estado} size="small" />
                    </div>
                    <div className="text-xs text-slate-500 mt-0.5">
                      Proveedor: <span className="font-medium text-slate-700">{req.nombre_proveedor}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-emerald-700">{req.fecha_entrega}</div>
                    <div className="text-[11px] text-slate-400">{req.total_lineas} producto(s)</div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Tarjeta: Productos con Inventario Bajo */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
              <h3 className="font-bold text-slate-900 text-base">Inventario Bajo (&lt; 50 unid.)</h3>
            </div>
            <Link to="/inventario" className="text-xs font-bold text-emerald-600 hover:text-emerald-700 flex items-center gap-1">
              Ver inventario <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="mt-4 flex-1 space-y-3">
            {lowStockProducts.length === 0 ? (
              <div className="py-8 text-center text-sm text-emerald-600 font-medium">
                ✅ Todos los productos tienen existencias suficientes
              </div>
            ) : (
              lowStockProducts.map((prod) => (
                <div
                  key={prod.id}
                  className="p-3.5 rounded-xl bg-amber-50/50 border border-amber-200 flex items-center justify-between"
                >
                  <div>
                    <span className="text-xs font-mono font-bold text-slate-500">{prod.codigo}</span>
                    <h4 className="text-sm font-semibold text-slate-800 leading-tight">{prod.nombre}</h4>
                  </div>
                  <div className="text-right pl-3">
                    <span className="text-base font-black text-amber-600">
                      {prod.cantidad}
                    </span>
                    <span className="text-xs text-slate-500 ml-1">unidades</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
