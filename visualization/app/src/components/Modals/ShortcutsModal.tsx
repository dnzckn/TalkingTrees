const SHORTCUTS = [
  { section: 'Simulation', items: [
    { keys: 'Space', desc: 'Play / Pause' },
    { keys: 'S', desc: 'Step one tick' },
    { keys: 'R', desc: 'Reset simulation' },
  ]},
  { section: 'Edit', items: [
    { keys: 'Delete', desc: 'Delete selected node(s)' },
    { keys: 'Ctrl+Z', desc: 'Undo' },
    { keys: 'Ctrl+Shift+Z', desc: 'Redo' },
    { keys: 'Ctrl+A', desc: 'Select all' },
    { keys: 'Ctrl+N', desc: 'New tree' },
    { keys: 'C', desc: 'Collapse / expand node' },
  ]},
  { section: 'View', items: [
    { keys: 'Ctrl+G', desc: 'Toggle grid' },
    { keys: 'Ctrl+Shift+D', desc: 'Toggle dataflow arrows' },
    { keys: 'Ctrl+Shift+T', desc: 'Toggle dark/light theme' },
    { keys: 'Ctrl+0', desc: 'Reset zoom & pan' },
    { keys: '+ / −', desc: 'Zoom in / out' },
    { keys: 'Alt+Drag', desc: 'Pan canvas' },
    { keys: 'Scroll', desc: 'Zoom toward cursor' },
  ]},
  { section: 'Canvas', items: [
    { keys: 'Right-click', desc: 'Context menu' },
    { keys: 'Drag bottom ●', desc: 'Connect nodes' },
    { keys: 'Shift+Click', desc: 'Multi-select' },
    { keys: 'Drag from palette', desc: 'Add node to canvas' },
    { keys: 'Double-click palette', desc: 'Quick-add node' },
  ]},
];

export function ShortcutsModal({ onClose }: { onClose: () => void }) {
  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'var(--surface-overlay)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10000,
    }} onClick={onClose}>
      <div style={{
        background: 'var(--surface-2)', border: '1px solid var(--border-1)',
        borderRadius: 'var(--r-lg)', padding: 0, width: 520, maxHeight: '80vh',
        boxShadow: '0 16px 64px rgba(0,0,0,0.6)', overflow: 'hidden',
      }} onClick={e => e.stopPropagation()}>
        <div style={{
          padding: '14px 20px', borderBottom: '1px solid var(--border-0)',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        }}>
          <span style={{ fontWeight: 700, fontSize: 'var(--fs-xl)' }}>Keyboard Shortcuts</span>
          <button onClick={onClose} style={{ background: 'transparent' }}>✕</button>
        </div>
        <div style={{ padding: '12px 20px', overflow: 'auto', maxHeight: '60vh' }}>
          {SHORTCUTS.map(s => (
            <div key={s.section} style={{ marginBottom: 16 }}>
              <div style={{ fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-2)', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: 6 }}>
                {s.section}
              </div>
              {s.items.map(i => (
                <div key={i.keys} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '4px 0', fontSize: 'var(--fs-sm)' }}>
                  <span style={{ color: 'var(--text-1)' }}>{i.desc}</span>
                  <kbd style={{
                    background: 'var(--surface-0)', border: '1px solid var(--border-1)', borderRadius: 3,
                    padding: '2px 8px', fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', color: 'var(--text-2)',
                  }}>{i.keys}</kbd>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
