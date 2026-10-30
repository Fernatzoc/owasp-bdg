import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { KeyRound, RefreshCw, AlertCircle, ArrowLeft, Sparkles, Check } from 'lucide-react';

export default function P02_OtpVerification() {
  const location = useLocation();
  const navigate = useNavigate();
  const { verifyOtp, resendOtp } = useAuth();

  const [currentTicket, setCurrentTicket] = useState(location.state?.loginTicket);
  const userEmail = location.state?.email || 'su correo';
  const [demoOtp, setDemoOtp] = useState(location.state?.demoOtp || null);

  // 6 casillas individuales
  const [digits, setDigits] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef([]);

  // Contador de expiración de OTP (5 minutos = 300 segundos)
  const [secondsLeft, setSecondsLeft] = useState(300);
  // Contador para reenviar (60 segundos)
  const [resendCooldown, setResendCooldown] = useState(60);
  const [canResend, setCanResend] = useState(false);

  const [attemptsRemaining, setAttemptsRemaining] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [infoMessage, setInfoMessage] = useState(null);

  // Redirigir al login si no hay ticket
  useEffect(() => {
    if (!currentTicket) {
      navigate('/login');
    }
  }, [currentTicket, navigate]);

  // Temporizador principal de 5:00
  useEffect(() => {
    if (secondsLeft <= 0) return;
    const interval = setInterval(() => {
      setSecondsLeft((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [secondsLeft]);

  // Temporizador de reenvío de 60s
  useEffect(() => {
    if (resendCooldown <= 0) {
      setCanResend(true);
      return;
    }
    const interval = setInterval(() => {
      setResendCooldown((prev) => prev - 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [resendCooldown]);

  const handleDigitChange = (index, value) => {
    if (value.length > 1) {
      // Manejar pegado de código completo
      const pasted = value.replace(/\D/g, '').slice(0, 6);
      if (pasted.length > 0) {
        const newDigits = [...digits];
        for (let i = 0; i < 6; i++) {
          newDigits[i] = pasted[i] || '';
        }
        setDigits(newDigits);
        const nextIndex = Math.min(pasted.length, 5);
        inputRefs.current[nextIndex]?.focus();
      }
      return;
    }

    const val = value.replace(/\D/g, '');
    const newDigits = [...digits];
    newDigits[index] = val;
    setDigits(newDigits);

    // Mover foco al siguiente input automáticamente
    if (val && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const fullOtp = digits.join('');

  const handleSubmit = async (e, codeOverride = null) => {
    e?.preventDefault();
    const codeToVerify = codeOverride || fullOtp;
    if (codeToVerify.length !== 6) {
      setError('Por favor ingrese los 6 dígitos del código OTP');
      return;
    }

    if (secondsLeft <= 0) {
      setError('El código OTP ha expirado. Por favor solicite uno nuevo.');
      return;
    }

    setError(null);
    setLoading(true);

    try {
      await verifyOtp(currentTicket, codeToVerify, false);
      navigate('/dashboard');
    } catch (err) {
      const resp = err.response?.data;
      if (err.response?.status === 409 && resp?.codigo === 'SESION_ACTIVA_EXISTENTE') {
        // Redirigir a P03 Aviso de sesión activa
        navigate('/sesion-activa', {
          state: {
            loginTicket: currentTicket,
            otp: codeToVerify,
            email: userEmail
          }
        });
        return;
      }

      const msg = resp?.mensaje || 'Error al validar el código OTP';
      setError(msg);

      // Decrementar intentos si fue incorrecto
      if (resp?.codigo === 'OTP_INCORRECTO') {
        setAttemptsRemaining((prev) => Math.max(0, prev - 1));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!canResend) return;
    setError(null);
    setLoading(true);

    try {
      const data = await resendOtp(currentTicket);
      if (data?.login_ticket) {
        setCurrentTicket(data.login_ticket);
      }
      if (data?.demo_otp) {
        setDemoOtp(data.demo_otp);
      }
      setInfoMessage('Se ha enviado un nuevo código OTP a su correo');
      setResendCooldown(60);
      setCanResend(false);
      setSecondsLeft(300);
      setAttemptsRemaining(3);
      setDigits(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (err) {
      const codigo = err.response?.data?.codigo;
      if (codigo === 'TOKEN_EXPIRADO') {
        setError('El tiempo de verificación ha expirado. Por favor inicie sesión nuevamente.');
      } else {
        setError(err.response?.data?.mensaje || 'No se pudo reenviar el código');
      }
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (secs) => {
    const mins = Math.floor(secs / 60);
    const s = secs % 60;
    return `${mins}:${s < 10 ? '0' : ''}${s}`;
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="w-12 h-12 mx-auto rounded-xl bg-emerald-600 flex items-center justify-center text-white font-bold shadow-lg">
          <KeyRound className="w-6 h-6" />
        </div>
        <h2 className="mt-4 text-center text-2xl font-black tracking-tight text-slate-900">
          Verificación de Doble Factor
        </h2>
        <p className="mt-2 text-center text-sm text-slate-600">
          Hemos enviado un código OTP de 6 dígitos a{' '}
          <span className="font-semibold text-slate-800">{userEmail}</span>
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

          {infoMessage && (
            <div className="mb-6 p-4 rounded-xl bg-blue-50 border border-blue-200 text-blue-800 text-sm">
              {infoMessage}
            </div>
          )}

          {demoOtp && (
            <div className="mb-6 p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 text-sm shadow-sm">
              <div className="flex items-center gap-2 font-bold mb-1 text-amber-900">
                <Sparkles className="w-4 h-4 text-amber-600" />
                <span>Modo Demostración / Evaluación</span>
              </div>
              <p className="text-xs text-amber-800 mb-2.5">
                Código OTP generado para esta cuenta de prueba:
              </p>
              <div className="flex items-center justify-between bg-white px-3.5 py-2.5 rounded-lg border border-amber-200 shadow-inner">
                <span className="font-mono text-2xl font-black tracking-widest text-emerald-600">
                  {demoOtp}
                </span>
                <button
                  type="button"
                  onClick={() => {
                    const chars = demoOtp.split('');
                    setDigits(chars);
                    handleSubmit(null, demoOtp);
                  }}
                  className="text-xs bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 shadow-sm"
                >
                  <Check className="w-3.5 h-3.5" />
                  Autocompletar
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-center text-sm font-semibold text-slate-700 mb-4">
                Ingrese el código de 6 dígitos
              </label>

              {/* 6 casillas de dígitos */}
              <div className="flex justify-center gap-2 sm:gap-3">
                {digits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (inputRefs.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    className="w-11 h-13 sm:w-12 sm:h-14 text-center text-2xl font-bold rounded-xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-500 outline-none transition-all bg-slate-50"
                  />
                ))}
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
              <div className="flex items-center gap-1.5 font-medium">
                <span>Vigencia:</span>
                <span className={`font-mono font-bold ${secondsLeft < 60 ? 'text-rose-600' : 'text-slate-700'}`}>
                  {formatTime(secondsLeft)}
                </span>
              </div>
              <div className="font-medium">
                Intentos restantes:{' '}
                <span className="font-bold text-slate-700">{attemptsRemaining}</span>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || fullOtp.length !== 6 || secondsLeft <= 0}
              className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Verificando...' : 'Confirmar e Iniciar Sesión'}
            </button>
          </form>

          <div className="mt-6 flex flex-col items-center gap-3">
            <button
              type="button"
              onClick={handleResend}
              disabled={!canResend || loading}
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-500 disabled:text-slate-400 flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${!canResend ? '' : 'text-emerald-600'}`} />
              {canResend
                ? 'Reenviar código de verificación'
                : `Reenviar código en ${resendCooldown}s`}
            </button>

            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-xs text-slate-500 hover:text-slate-700 flex items-center gap-1 mt-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Volver al inicio de sesión
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
