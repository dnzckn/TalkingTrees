import { useState, useCallback } from 'react';

interface ToastMsg { id: number; text: string; type: 'info' | 'success' | 'warning' | 'error' }

let _addToast: (text: string, type?: ToastMsg['type']) => void = () => {};
export function showToast(text: string, type: ToastMsg['type'] = 'info') { _addToast(text, type); }

const COLORS = { info: 'var(--accent)', success: 'var(--success)', warning: 'var(--running)', error: 'var(--failure)' };

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMsg[]>([]);
  let nextId = 0;

  _addToast = useCallback((text: string, type: ToastMsg['type'] = 'info') => {
    const id = ++nextId;
    setToasts(t => [...t, { id, text, type }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 2500);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div style={{ position: 'fixed', top: 52, right: 16, zIndex: 10000, display: 'flex', flexDirection: 'column', gap: 6 }}>
      {toasts.map(t => (
        <div key={t.id} style={{
          padding: '8px 14px', borderRadius: 'var(--r-md)',
          background: 'var(--s3)', border: `1px solid ${COLORS[t.type]}`,
          boxShadow: '0 4px 16px rgba(0,0,0,0.4)', fontSize: 'var(--fs-sm)',
          color: 'var(--t0)', maxWidth: 320, animation: 'fadeIn 0.2s ease',
          borderLeft: `3px solid ${COLORS[t.type]}`,
        }}>
          {t.text}
        </div>
      ))}
      <style>{`@keyframes fadeIn { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: none; } }`}</style>
    </div>
  );
}
