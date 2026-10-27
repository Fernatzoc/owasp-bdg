import React, { useState } from 'react';
import { ShieldCheck, RefreshCw, CheckCircle2 } from 'lucide-react';

export default function Captcha({ onVerify, verified = false }) {
  const [loading, setLoading] = useState(false);
  const [isChecked, setIsChecked] = useState(verified);

  const handleCheckboxClick = () => {
    if (isChecked || loading) return;
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setIsChecked(true);
      if (onVerify) {
        onVerify('test-captcha-token-' + Date.now());
      }
    }, 600);
  };

  return (
    <div className="flex items-center justify-between p-3.5 bg-slate-50 border border-slate-300 rounded-lg shadow-sm w-full max-w-sm select-none">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleCheckboxClick}
          className={`w-7 h-7 rounded border flex items-center justify-center transition-all ${
            isChecked
              ? 'bg-emerald-600 border-emerald-600 text-white'
              : 'border-slate-400 bg-white hover:border-slate-600'
          }`}
          disabled={isChecked || loading}
        >
          {loading && <RefreshCw className="w-4 h-4 text-emerald-600 animate-spin" />}
          {isChecked && <CheckCircle2 className="w-5 h-5 text-white" />}
        </button>
        <span className="text-sm font-medium text-slate-700 cursor-pointer" onClick={handleCheckboxClick}>
          No soy un robot
        </span>
      </div>

      <div className="flex flex-col items-center pl-4 border-l border-slate-200">
        <ShieldCheck className="w-6 h-6 text-emerald-600" />
        <span className="text-[10px] text-slate-400 font-semibold tracking-wider">reCAPTCHA</span>
        <span className="text-[9px] text-slate-400">Privacidad · Términos</span>
      </div>
    </div>
  );
}
