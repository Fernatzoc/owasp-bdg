import React, { useState, useEffect } from 'react';
import api from '../api/client';
import ConfirmModal from '../components/ConfirmModal';
import Toast from '../components/Toast';
import {
  Users,
  Search,
  Shield,
  UserCheck,
  UserX,
  Lock,
  LogOut,
  Edit,
  X
} from 'lucide-react';

const ROLES_DISPONIBLES = ['Administrador', 'Compras', 'Proveedor', 'Bodega', 'Consulta'];

export default function P08_UsersRoles() {
  const [users, setUsers] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Filtros
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Modales y acciones
  const [editRoleUser, setEditRoleUser] = useState(null);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [selectedSupplierId, setSelectedSupplierId] = useState('');
  const [modalLoading, setModalLoading] = useState(false);

  // Confirmación
  const [confirmData, setConfirmData] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    fetchUsers();
    fetchSuppliers();
  }, [roleFilter, statusFilter]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('query', search);
      if (roleFilter) params.append('rol', roleFilter);
      if (statusFilter) params.append('estado', statusFilter);

      const res = await api.get(`/users?${params.toString()}`);
      setUsers(res.data.items || []);
    } catch (err) {
      setToast({ type: 'error', message: 'Error cargando usuarios' });
    } finally {
      setLoading(false);
    }
  };

  const fetchSuppliers = async () => {
    try {
      const res = await api.get('/suppliers?size=100&activo=true');
      setSuppliers(res.data.items || []);
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenEditRoles = (user) => {
    setEditRoleUser(user);
    setSelectedRoles(user.roles || []);
    setSelectedSupplierId(user.proveedor_id || '');
  };

  const handleRoleToggle = (rol) => {
    if (selectedRoles.includes(rol)) {
      setSelectedRoles(selectedRoles.filter((r) => r !== rol));
    } else {
      setSelectedRoles([...selectedRoles, rol]);
    }
  };

  const handleSaveRoles = async (e) => {
    e.preventDefault();
    if (selectedRoles.length === 0) {
      setToast({ type: 'error', message: 'El usuario debe tener al menos un rol' });
      return;
    }

    if (selectedRoles.includes('Proveedor') && !selectedSupplierId) {
      setToast({ type: 'error', message: 'Debe vincular un proveedor al asignar el rol Proveedor' });
      return;
    }

    setModalLoading(true);
    try {
      await api.patch(`/users/${editRoleUser.id}/roles`, {
        roles: selectedRoles,
        proveedor_id: selectedRoles.includes('Proveedor') ? selectedSupplierId : null
      });
      setToast({ type: 'success', message: 'Roles actualizados exitosamente' });
      setEditRoleUser(null);
      fetchUsers();
    } catch (err) {
      setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error actualizando roles' });
    } finally {
      setModalLoading(false);
    }
  };

  const handleStatusChange = (user, nuevoEstado) => {
    setConfirmData({
      title: `Cambiar estado a '${nuevoEstado}'`,
      message: `¿Está seguro de cambiar el estado de ${user.nombre} a ${nuevoEstado}?`,
      onConfirm: async () => {
        try {
          await api.patch(`/users/${user.id}`, { estado: nuevoEstado });
          setToast({ type: 'success', message: `Usuario actualizado a ${nuevoEstado}` });
          setConfirmData(null);
          fetchUsers();
        } catch (err) {
          setToast({ type: 'error', message: err.response?.data?.mensaje || 'Error al cambiar estado' });
        }
      }
    });
  };

  const handleForceLogout = (user) => {
    setConfirmData({
      title: 'Forzar Cierre de Sesión',
      message: `¿Desea cerrar forzosamente todas las sesiones activas de ${user.nombre}?`,
      isDanger: true,
      onConfirm: async () => {
        try {
          const res = await api.post(`/users/${user.id}/force-logout`);
          setToast({ type: 'success', message: res.data.mensaje || 'Sesiones cerradas' });
          setConfirmData(null);
          fetchUsers();
        } catch (err) {
          setToast({ type: 'error', message: 'Error cerrando sesiones' });
        }
      }
    });
  };

  return (
    <div className="space-y-6">
      <Toast toast={toast} onClose={() => setToast(null)} />
      <ConfirmModal
        isOpen={!!confirmData}
        title={confirmData?.title}
        message={confirmData?.message}
        isDanger={confirmData?.isDanger}
        onConfirm={confirmData?.onConfirm}
        onCancel={() => setConfirmData(null)}
      />

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            <Users className="w-7 h-7 text-emerald-600" />
            Gestión de Usuarios y Roles
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Administre cuentas, asigne permisos y controle sesiones activas
          </p>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Buscar por nombre o correo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchUsers()}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>

        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos los roles</option>
          {ROLES_DISPONIBLES.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-sm border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="pendiente">Pendiente de verificación</option>
          <option value="bloqueado">Bloqueado</option>
          <option value="inactivo">Inactivo</option>
        </select>

        <button
          onClick={fetchUsers}
          className="px-4 py-2 bg-slate-800 text-white font-bold text-sm rounded-lg hover:bg-slate-900"
        >
          Buscar
        </button>
      </div>

      {/* Tabla de Usuarios */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold uppercase tracking-wider text-slate-500">
                <th className="py-3 px-4">Usuario</th>
                <th className="py-3 px-4">Roles Asignados</th>
                <th className="py-3 px-4">Proveedor Vinculado</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400">
                    Cargando usuarios...
                  </td>
                </tr>
              ) : users.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400">
                    No se encontraron usuarios
                  </td>
                </tr>
              ) : (
                users.map((u) => {
                  const provVinculado = suppliers.find((s) => s.id === u.proveedor_id);

                  return (
                    <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-900">{u.nombre}</div>
                        <div className="text-xs text-slate-500">{u.email}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex flex-wrap gap-1">
                          {u.roles?.map((r) => (
                            <span
                              key={r}
                              className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800"
                            >
                              {r}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-xs text-slate-600">
                        {provVinculado ? (
                          <span className="font-semibold text-slate-800">
                            {provVinculado.codigo} - {provVinculado.nombre}
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                            u.estado === 'activo'
                              ? 'bg-emerald-100 text-emerald-800'
                              : u.estado === 'bloqueado'
                              ? 'bg-rose-100 text-rose-800'
                              : u.estado === 'pendiente'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {u.estado}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenEditRoles(u)}
                            title="Editar roles y proveedor"
                            className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                          >
                            <Edit className="w-4 h-4" />
                          </button>

                          {u.estado === 'activo' ? (
                            <button
                              onClick={() => handleStatusChange(u, 'inactivo')}
                              title="Desactivar cuenta"
                              className="p-1.5 text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                            >
                              <UserX className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleStatusChange(u, 'activo')}
                              title="Activar cuenta"
                              className="p-1.5 text-slate-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                            >
                              <UserCheck className="w-4 h-4" />
                            </button>
                          )}

                          <button
                            onClick={() => handleForceLogout(u)}
                            title="Forzar cierre de sesión"
                            className="p-1.5 text-slate-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
                          >
                            <LogOut className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Asignar Roles */}
      {editRoleUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-2xl shadow-xl max-w-md w-full overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between p-5 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-lg">Asignar Roles de Usuario</h3>
              <button
                onClick={() => setEditRoleUser(null)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveRoles} className="p-6 space-y-5">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs text-slate-600">
                Usuario: <span className="font-bold text-slate-900">{editRoleUser.nombre}</span> ({editRoleUser.email})
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2">
                  Seleccione uno o más roles:
                </label>
                <div className="space-y-2">
                  {ROLES_DISPONIBLES.map((rol) => (
                    <label
                      key={rol}
                      className="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-50 cursor-pointer border border-slate-100"
                    >
                      <input
                        type="checkbox"
                        checked={selectedRoles.includes(rol)}
                        onChange={() => handleRoleToggle(rol)}
                        className="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                      />
                      <span className="text-sm font-medium text-slate-800">{rol}</span>
                    </label>
                  ))}
                </div>
              </div>

              {selectedRoles.includes('Proveedor') && (
                <div className="pt-2">
                  <label className="block text-sm font-semibold text-slate-700 mb-1">
                    Vincular a Proveedor:
                  </label>
                  <select
                    value={selectedSupplierId}
                    onChange={(e) => setSelectedSupplierId(e.target.value)}
                    required
                    className="w-full text-sm border border-slate-300 rounded-lg p-2.5 outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    <option value="">Seleccione un proveedor...</option>
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.codigo} - {s.nombre}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditRoleUser(null)}
                  className="px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 rounded-lg"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 bg-emerald-600 text-white font-bold text-sm rounded-lg hover:bg-emerald-700 shadow-sm"
                >
                  {modalLoading ? 'Guardando...' : 'Guardar Cambios'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
