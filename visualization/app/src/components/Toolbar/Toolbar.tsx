import { useUIStore } from '../../store/uiStore';
import { useTreeStore } from '../../store/treeStore';

export function Toolbar() {
  const ui = useUIStore();
  const { clear, treeName } = useTreeStore();

  const handleNew = () => { if (confirm('Create new tree?')) clear(); };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file'; input.accept = '.json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        useTreeStore.getState().loadTree(JSON.parse(await file.text()));
      } catch { alert('Invalid tree JSON'); }
    };
    input.click();
  };

  const handleExport = () => {
    try {
      const def = useTreeStore.getState().exportTree();
      const blob = new Blob([JSON.stringify(def, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `${treeName.replace(/\s+/g, '_').toLowerCase()}.json`;
      a.click();
    } catch (err) { alert(`Export error: ${err}`); }
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 2,
      height: 'var(--toolbar-h)', padding: '0 10px',
      background: 'linear-gradient(180deg, var(--surface-2) 0%, var(--surface-1) 100%)',
      borderBottom: '1px solid var(--border-0)',
      fontSize: 'var(--fs-sm)',
    }}>
      {/* Logo */}
      <div style={{ fontWeight: 700, fontSize: 'var(--fs-lg)', marginRight: 8, color: 'var(--accent)', letterSpacing: '-0.3px' }}>
        🌳 TalkingTrees
      </div>

      <Sep />
      <Grp>
        <Btn onClick={handleNew} tip="New Tree">📄 New</Btn>
        <Btn onClick={handleImport} tip="Import JSON">📂 Open</Btn>
        <Btn onClick={handleExport} tip="Export JSON">💾 Save</Btn>
      </Grp>

      <Sep />
      <Grp>
        <Btn onClick={() => ui.togglePanel('palette')} tip="Toggle palette" on={ui.showPalette}>◧ Palette</Btn>
        <Btn onClick={() => ui.togglePanel('properties')} tip="Toggle properties" on={ui.showProperties}>⚙ Props</Btn>
        <Btn onClick={() => ui.togglePanel('grid')} tip="Toggle grid (Ctrl+G)" on={ui.showGrid}>▦ Grid</Btn>
        <Btn onClick={() => ui.togglePanel('dataflow')} tip="Show BB flow arrows" on={ui.showDataflow}>⇢ Flow</Btn>
        <Btn onClick={() => ui.togglePanel('timeline')} tip="Toggle timeline" on={ui.showTimeline}>▬ Timeline</Btn>
      </Grp>

      <Sep />
      <Btn onClick={ui.toggleTheme} tip="Toggle theme (Ctrl+Shift+T)">
        {ui.theme === 'dark' ? '☀' : '🌙'}
      </Btn>

      <div style={{ flex: 1 }} />

      {/* Zoom controls */}
      <Grp>
        <Btn onClick={() => ui.setZoom(ui.zoom * 0.85)}>−</Btn>
        <span style={{ color: 'var(--text-2)', fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', width: 36, textAlign: 'center' }}>
          {Math.round(ui.zoom * 100)}%
        </span>
        <Btn onClick={() => ui.setZoom(ui.zoom * 1.15)}>+</Btn>
        <Btn onClick={() => { ui.setZoom(1); ui.setPan(0, 0); }} tip="Reset view">⊡</Btn>
      </Grp>

      <Sep />
      <span style={{ color: 'var(--text-2)', fontSize: 'var(--fs-xs)' }}>{treeName}</span>
    </div>
  );
}

function Grp({ children }: { children: React.ReactNode }) {
  return <div style={{ display: 'flex', gap: 1 }}>{children}</div>;
}
function Sep() {
  return <div style={{ width: 1, height: 18, background: 'var(--border-0)', margin: '0 6px' }} />;
}
function Btn({ children, onClick, tip, on }: { children: React.ReactNode; onClick: () => void; tip?: string; on?: boolean }) {
  return (
    <button onClick={onClick} title={tip} style={{
      background: on ? 'var(--accent-dim)' : undefined,
      color: on ? 'var(--accent)' : undefined,
      borderRadius: 'var(--r-sm)',
    }}>
      {children}
    </button>
  );
}
