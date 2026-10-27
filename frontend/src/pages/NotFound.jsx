import React from 'react';
import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center items-center px-4">
      <div className="text-center max-w-md">
        <h1 className="text-7xl font-black text-slate-900 tracking-tight">404</h1>
        <h2 className="text-2xl font-bold text-slate-800 mt-2">Página no encontrada</h2>
        <p className="text-sm text-slate-500 mt-2">
          La ruta solicitada no existe o no cuenta con los permisos necesarios.
        </p>
        <div className="mt-6">
          <Link
            to="/dashboard"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-700 shadow-sm transition-colors"
          >
            <Home className="w-4 h-4" />
            Volver al Panel Principal
          </Link>
        </div>
      </div>
    </div>
  );
}
