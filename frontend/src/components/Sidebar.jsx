import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Users,
  Package,
  Building2,
  ClipboardList,
  Boxes,
  ArrowLeftRight,
  ShieldAlert,
  X
} from 'lucide-react';

export default function Sidebar({ isOpen, onClose }) {
  const { hasAnyRole, hasRole } = useAuth();

  const navItems = [
    {
      to: '/dashboard',
      label: 'Panel de Inicio',
      icon: LayoutDashboard,
      allowed: true // Todos
    },
    {
      to: '/solicitudes',
      label: 'Solicitudes',
      icon: ClipboardList,
      allowed: hasAnyRole(['Compras', 'Proveedor', 'Bodega', 'Administrador'])
    },
    {
      to: '/inventario',
      label: 'Inventario',
      icon: Boxes,
      allowed: hasAnyRole(['Consulta', 'Bodega', 'Compras', 'Administrador'])
    },
    {
      to: '/movimientos',
      label: 'Movimientos',
      icon: ArrowLeftRight,
      allowed: true // Todos (con alcance para proveedor)
    },
    {
      to: '/productos',
      label: 'Productos',
      icon: Package,
      allowed: hasAnyRole(['Consulta', 'Compras', 'Bodega', 'Administrador'])
    },
    {
      to: '/proveedores',
      label: 'Proveedores',
      icon: Building2,
      allowed: hasAnyRole(['Compras', 'Administrador'])
    },
    {
      to: '/usuarios',
      label: 'Usuarios y Roles',
      icon: Users,
      allowed: hasRole('Administrador')
    },
    {
      to: '/bitacora',
      label: 'Bitácora de Seguridad',
      icon: ShieldAlert,
      allowed: hasRole('Administrador')
    }
  ];

  const visibleItems = navItems.filter(item => item.allowed);

  return (
    <>
      {/* Overlay para móviles */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
        />
      )}

      <aside
        className={`fixed lg:static top-0 bottom-0 left-0 z-40 w-64 bg-slate-900 text-slate-300 flex flex-col transition-transform duration-300 ease-in-out ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex items-center justify-between h-16 px-6 bg-slate-950 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-black text-lg shadow-inner">
              B
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-white tracking-wide text-sm leading-tight">BDG Logística</span>
              <span className="text-[10px] text-emerald-400 font-semibold tracking-wider uppercase">Portal Proveedores</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 rounded-lg lg:hidden hover:text-white hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
          <div className="px-3 mb-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Navegación
          </div>
          {visibleItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => {
                  if (window.innerWidth < 1024) onClose();
                }}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="p-4 border-t border-slate-800 text-xs text-slate-400 text-center">
          Prototipo v1.0 · 2026
        </div>
      </aside>
    </>
  );
}
