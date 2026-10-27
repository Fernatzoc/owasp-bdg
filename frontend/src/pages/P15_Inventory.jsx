import React, { useState, useEffect } from 'react';
import api from '../api/client';
import Toast from '../components/Toast';
import {
  Boxes,
  Search,
  Download,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  AlertTriangle
} from 'lucide-react';

export default function P15_Inventory() {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Parámetros de consulta
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('codigo');
  const [sortOrder, setSortOrder] = useState(1); // 1 asc, -1 desc
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchInventory();
  }, [sortBy, sortOrder, page]);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('query', search);
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder.toString());
      params.append('page', page.toString());
      params.append('size', '20');

      const res = await api.get(`/inventory?${params.toString()}`);
      setInventory(res.data.items || []);
      setTotal(res.data.total || 0);
      setTotalPages(res.data.pages || 1);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando datos de inventario' });
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 1 ? -1 : 1);
    } else {
      setSortBy(field);
      setSortOrder(1);
    }
  };

  const handleExportCSV = async () => {
    try {
      const res = await api.get('/inventory/export', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `inventario_${new Date().toISOString().split('T')[0]}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      setToast({ type: 'success', message: 'Archivo CSV descargado exitosamente' });
    } catch (err) {
      setToast({ type: 'error', message: 'Error exportando inventario' });
    }
  };

  const renderSortIcon = (field) => {
    if (sortBy !== field) return <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />;
    return sortOrder === 1 ? (
      <ArrowUp className="w-3.5 h-3.5 text-emerald-600" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-emerald-600" />
    );
  };

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <Boxes className="w-7 h-7 text-emerald-600" />
            Consulta de Inventario
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Control de existencias disponibles en bodega física
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 text-white font-bold text-sm rounded-xl hover:bg-slate-900 shadow-sm transition-colors"
        >
          <Download className="w-4 h-4" />
          Exportar a CSV / Excel
        </button>
      </div>

      {/* Barra de Búsqueda */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Buscar producto por código o nombre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                setPage(1);
                fetchInventory();
              }
            }}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <button
          onClick={() => {
            setPage(1);
            fetchInventory();
          }}
          className="px-5 py-2 bg-emerald-600 text-white font-bold text-sm rounded-lg hover:bg-emerald-700 shadow-sm transition-colors"
        >
          Buscar
        </button>
      </div>

      {/* Tabla de Existencias */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500 select-none">
                <th
                  onClick={() => handleSort('codigo')}
                  className="py-3 px-4 cursor-pointer hover:bg-slate-100/70"
                >
                  <div className="flex items-center gap-1.5">
                    Código {renderSortIcon('codigo')}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('nombre')}
                  className="py-3 px-4 cursor-pointer hover:bg-slate-100/70"
                >
                  <div className="flex items-center gap-1.5">
                    Producto {renderSortIcon('nombre')}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('cantidad')}
                  className="py-3 px-4 text-right cursor-pointer hover:bg-slate-100/70"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    Cantidad Disponible {renderSortIcon('cantidad')}
                  </div>
                </th>
                <th
                  onClick={() => handleSort('actualizado_en')}
                  className="py-3 px-4 text-right cursor-pointer hover:bg-slate-100/70"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    Última Actualización {renderSortIcon('actualizado_en')}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-slate-400">
                    Cargando inventario...
                  </td>
                </tr>
              ) : inventory.length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-12 text-center text-slate-400">
                    No hay productos en inventario
                  </td>
                </tr>
              ) : (
                inventory.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-bold text-slate-900">
                      {item.codigo}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-800">
                      {item.nombre}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <span
                        className={`text-base font-black ${
                          item.cantidad <= 20
                            ? 'text-rose-600'
                            : item.cantidad < 50
                            ? 'text-amber-600'
                            : 'text-emerald-700'
                        }`}
                      >
                        {item.cantidad.toLocaleString('es-GT', { minimumFractionDigits: 0 })}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right text-xs text-slate-500">
                      {item.actualizado_en ? new Date(item.actualizado_en).toLocaleString('es-GT') : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-6 py-3 bg-slate-50 border-t border-slate-100 text-xs text-slate-500">
            <span>Total: <strong>{total}</strong> productos registrados</span>
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
