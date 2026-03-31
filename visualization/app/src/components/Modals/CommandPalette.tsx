import { useState, useEffect, useRef } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { useSimStore } from '../../store/simulationStore';
import { useHistoryStore } from '../../store/historyStore';
import { computeLayout } from '../../services/layout';
import { showToast } from '../Panels/Toast';

interface Cmd { id: string; label: string; shortcut?: string; section: string; action: () => void }

function getCommands(): Cmd[] {
  return [
    { id: 'new', label: 'New Tree', shortcut: 'Ctrl+N', section: 'File', action: () => { useHistoryStore.getState().save(); useTreeStore.getState().clear(); } },
    { id: 'layout', label: 'Auto Layout', shortcut: 'Ctrl+L', section: 'Edit', action: () => {
      useHistoryStore.getState().save();
      const pos = computeLayout(useTreeStore.getState().nodes);
      for (const [id, p] of Object.entries(pos)) useTreeStore.getState().updateNode(id, p);
      showToast('Layout applied', 'success');
    }},
    { id: 'undo', label: 'Undo', shortcut: 'Ctrl+Z', section: 'Edit', action: () => useHistoryStore.getState().undo() },
    { id: 'redo', label: 'Redo', shortcut: 'Ctrl+Shift+Z', section: 'Edit', action: () => useHistoryStore.getState().redo() },
    { id: 'grid', label: 'Toggle Grid', shortcut: 'Ctrl+G', section: 'View', action: () => useUIStore.getState().togglePanel('grid') },
    { id: 'dataflow', label: 'Toggle Dataflow', shortcut: 'Ctrl+Shift+D', section: 'View', action: () => useUIStore.getState().togglePanel('dataflow') },
    { id: 'theme', label: 'Toggle Theme', shortcut: 'Ctrl+Shift+T', section: 'View', action: () => useUIStore.getState().toggleTheme() },
    { id: 'validate', label: 'Validate Tree', shortcut: 'Ctrl+Shift+V', section: 'Tools', action: () => window.dispatchEvent(new CustomEvent('show-validation')) },
    { id: 'bb', label: 'Blackboard Inspector', section: 'Tools', action: () => window.dispatchEvent(new CustomEvent('show-blackboard')) },
    { id: 'shortcuts', label: 'Keyboard Shortcuts', shortcut: 'F1', section: 'Help', action: () => window.dispatchEvent(new CustomEvent('show-shortcuts')) },
    { id: 'play', label: 'Play / Pause Simulation', shortcut: 'Space', section: 'Simulation', action: () => { const s = useSimStore.getState(); s.running ? s.pause() : s.play(); } },
    { id: 'step', label: 'Step Simulation', shortcut: 'S', section: 'Simulation', action: () => useSimStore.getState().step() },
    { id: 'reset', label: 'Reset Simulation', shortcut: 'R', section: 'Simulation', action: () => useSimStore.getState().reset() },
  ];
}

export function CommandPalette({ onClose }: { onClose: () => void }) {
  const [query, setQuery] = useState('');
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const commands = getCommands();

  const filtered = query
    ? commands.filter(c => c.label.toLowerCase().includes(query.toLowerCase()) || c.section.toLowerCase().includes(query.toLowerCase()))
    : commands;

  useEffect(() => { inputRef.current?.focus(); }, []);
  useEffect(() => { setSelectedIdx(0); }, [query]);

  const run = (cmd: Cmd) => { cmd.action(); onClose(); };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx(i => Math.min(i + 1, filtered.length - 1)); }
    if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIdx(i => Math.max(i - 1, 0)); }
    if (e.key === 'Enter' && filtered[selectedIdx]) { run(filtered[selectedIdx]); }
    if (e.key === 'Escape') onClose();
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'var(--s-overlay)', zIndex: 10000, display: 'flex', justifyContent: 'center', paddingTop: '15vh' }}
      onClick={onClose}
    >
      <div style={{
        width: 480, maxHeight: '50vh', background: 'var(--s2)', border: '1px solid var(--b1)',
        borderRadius: 'var(--r-lg)', overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.7)',
        display: 'flex', flexDirection: 'column',
      }} onClick={e => e.stopPropagation()}>
        {/* Search */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--b0)' }}>
          <input ref={inputRef} value={query} onChange={e => setQuery(e.target.value)} onKeyDown={handleKey}
            placeholder="Type a command..." style={{ width: '100%', padding: '8px 12px', fontSize: 'var(--fs-lg)', background: 'var(--s0)', border: '1px solid var(--b1)', borderRadius: 'var(--r-md)' }}
          />
        </div>
        {/* Results */}
        <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
          {filtered.map((cmd, i) => (
            <div key={cmd.id} onClick={() => run(cmd)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10, padding: '8px 16px', cursor: 'pointer',
                background: i === selectedIdx ? 'var(--s-hover)' : 'transparent',
                borderLeft: i === selectedIdx ? '2px solid var(--accent)' : '2px solid transparent',
              }}
              onMouseEnter={() => setSelectedIdx(i)}
            >
              <span style={{ color: 'var(--t2)', fontSize: 'var(--fs-xs)', fontWeight: 600, width: 60, textTransform: 'uppercase' }}>{cmd.section}</span>
              <span style={{ flex: 1, color: 'var(--t0)' }}>{cmd.label}</span>
              {cmd.shortcut && <kbd style={{
                background: 'var(--s0)', border: '1px solid var(--b1)', borderRadius: 3,
                padding: '2px 7px', fontFamily: 'var(--mono)', fontSize: 'var(--fs-xs)', color: 'var(--t2)',
              }}>{cmd.shortcut}</kbd>}
            </div>
          ))}
          {filtered.length === 0 && <div style={{ padding: 16, textAlign: 'center', color: 'var(--t3)' }}>No matching commands</div>}
        </div>
      </div>
    </div>
  );
}
