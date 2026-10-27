import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api/client';
import Captcha from '../components/Captcha';
import { UserPlus, User, Mail, Lock, Check, X, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function P04_Register() {
  const [nombre, setNombre] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [registeredEmail, setRegisteredEmail] = useState(null);
  const [verifyToken, setVerifyToken] = useState(null);

  // Reglas de la política de contraseñas (RF-SEG-01)
  const rules = {
    length: password.length >= 8,
    uppercase: /[A-Z]/.test(password),
    lowercase: /[a-z]/.test(password),
    number: /\d/.test(password),
    symbol: /[^A-Za-z0-9]/.test(password),
  };

  const strengthCount = Object.values(rules).filter(Boolean).length;
  const strengthLevels = ['Muy débil', 'Débil', 'Media', 'Buena', 'Fuerte'];
  const strengthColors = ['bg-rose-500', 'bg-rose-400', 'bg-amber-400', 'bg-emerald-400', 'bg-emerald-600'];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!nombre.trim()) {
      setError('Por favor ingrese su nombre completo');
      return;
    }

    if (!email.trim()) {
      setError('Por favor ingrese su correo electrónico');
      return;
    }

    if (!password) {
      setError('Por favor ingrese una contraseña');
      return;
    }

    if (strengthCount < 5) {
      setError('La contraseña debe cumplir con los 5 requisitos de seguridad (mínimo 8 caracteres, mayúscula, minúscula, número y símbolo)');
      return;
    }

    if (!confirmPassword) {
      setError('Por favor confirme su contraseña');
      return;
    }

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (!captchaToken) {
      setError('Por favor complete la verificación de seguridad (Captcha)');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const resp = await api.post('/auth/register', {
        nombre: nombre.trim(),
        email: email.trim(),
        password,
        confirm_password: confirmPassword,
        captcha_token: captchaToken,
      });

      if (resp.data?.verify_token) {
        setVerifyToken(resp.data.verify_token);
      }
      setRegisteredEmail(email.trim());
    } catch (err) {
      setError(err.response?.data?.mensaje || 'Error al procesar el registro');
    } finally {
      setLoading(false);
    }
  };

  if (registeredEmail) {
    return (
      <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-10 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200 text-center">
            <div className="w-16 h-16 mx-auto rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-10 h-10" />
            </div>
            <h2 className="text-2xl font-black text-slate-900">¡Registro Exitoso!</h2>
            <p className="mt-3 text-sm text-slate-600 leading-relaxed">
              Hemos enviado un enlace de confirmación a <span className="font-semibold text-slate-800">{registeredEmail}</span>.
            </p>
            {verifyToken ? (
              <div className="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 text-left">
                <strong>Modo Evaluación / Pruebas:</strong>
                <p className="mt-1">
                  Puede activar su nueva cuenta de inmediato haciendo clic abajo:
                </p>
                <div className="mt-3">
                  <Link
                    to={`/verificar-email?token=${verifyToken}`}
                    className="w-full inline-flex justify-center py-2.5 px-4 rounded-lg bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-700 shadow-sm transition-colors"
                  >
                    Activar Cuenta Ahora
                  </Link>
                </div>
              </div>
            ) : (
              <div className="mt-4 p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 text-left">
                Por favor revise su bandeja de entrada (y carpeta de spam) para activar su cuenta.
              </div>
            )}
            <div className="mt-6">
              <Link
                to="/login"
                className="w-full inline-flex justify-center py-2.5 px-4 rounded-lg bg-slate-100 text-slate-700 font-bold text-sm hover:bg-slate-200 shadow-sm transition-colors"
              >
                Ir a Iniciar Sesión
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-600 flex items-center justify-center text-white font-bold shadow-lg">
          <UserPlus className="w-6 h-6" />
        </div>
        <h2 className="mt-4 text-center text-2xl font-black tracking-tight text-slate-900">
          Crear una Cuenta
        </h2>
        <p className="mt-1 text-center text-sm text-slate-600">
          Registro de usuario nuevo en el portal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-slate-700">Nombre Completo</label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <User className="h-5 w-5 text-slate-400" />
                </div>
                <input
                  type="text"
                  required
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  placeholder="Juan Pérez"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700">Correo Electrónico</label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Mail className="h-5 w-5 text-slate-400" />
                </div>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ejemplo@empresa.com"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700">Contraseña</label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-400" />
                </div>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                />
              </div>

              {/* Medidor de Fortaleza de Contraseña */}
              {password && (
                <div className="mt-2.5">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] font-semibold text-slate-500">Fortaleza:</span>
                    <span className="text-[11px] font-bold text-slate-700">
                      {strengthLevels[Math.max(0, strengthCount - 1)]}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-slate-200 rounded-full overflow-hidden flex gap-1">
                    {[1, 2, 3, 4, 5].map((level) => (
                      <div
                        key={level}
                        className={`h-full flex-1 transition-all ${
                          strengthCount >= level
                            ? strengthColors[strengthCount - 1]
                            : 'bg-transparent'
                        }`}
                      />
                    ))}
                  </div>

                  {/* Reglas visuales */}
                  <div className="mt-2 grid grid-cols-2 gap-1 text-[11px]">
                    <div className={`flex items-center gap-1 ${rules.length ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {rules.length ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-slate-400" />}
                      Mínimo 8 caracteres
                    </div>
                    <div className={`flex items-center gap-1 ${rules.uppercase ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {rules.uppercase ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-slate-400" />}
                      Una mayúscula
                    </div>
                    <div className={`flex items-center gap-1 ${rules.lowercase ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {rules.lowercase ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-slate-400" />}
                      Una minúscula
                    </div>
                    <div className={`flex items-center gap-1 ${rules.number ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {rules.number ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-slate-400" />}
                      Un número
                    </div>
                    <div className={`flex items-center gap-1 col-span-2 ${rules.symbol ? 'text-emerald-700' : 'text-slate-500'}`}>
                      {rules.symbol ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <X className="w-3.5 h-3.5 text-slate-400" />}
                      Un símbolo especial (!@#$%^&*)
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700">Confirmar Contraseña</label>
              <div className="mt-1 relative rounded-lg shadow-sm">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Lock className="h-5 w-5 text-slate-400" />
                </div>
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none"
                />
              </div>
              {confirmPassword && (
                <p className={`text-xs mt-1.5 flex items-center gap-1 font-medium ${password === confirmPassword ? 'text-emerald-600' : 'text-rose-500'}`}>
                  {password === confirmPassword ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" /> Las contraseñas coinciden
                    </>
                  ) : (
                    <>
                      <X className="w-3.5 h-3.5 text-rose-500" /> Las contraseñas no coinciden
                    </>
                  )}
                </p>
              )}
            </div>

            <div className="pt-2">
              <Captcha onVerify={setCaptchaToken} />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition-colors mt-2 cursor-pointer"
            >
              {loading ? 'Registrando cuenta...' : 'Crear Cuenta'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <span className="text-sm text-slate-600">¿Ya tiene una cuenta? </span>
            <Link to="/login" className="text-sm font-bold text-emerald-600 hover:text-emerald-500">
              Iniciar Sesión
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
