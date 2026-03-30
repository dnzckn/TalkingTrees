import { useUIStore } from '../../store/uiStore';
import { useTreeStore } from '../../store/treeStore';
import { useHistoryStore } from '../../store/historyStore';
import { computeLayout } from '../../services/layout';
import { showToast } from '../Panels/Toast';

export function Toolbar() {
  const ui = useUIStore();
  const { clear, treeName, nodes } = useTreeStore();
  const history = useHistoryStore();

  const handleNew = () => { if (confirm('Create new tree?')) { history.save(); clear(); showToast('New tree created'); } };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file'; input.accept = '.json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        history.save();
        useTreeStore.getState().loadTree(JSON.parse(await file.text()));
        showToast(`Loaded "${file.name}"`, 'success');
      } catch { showToast('Invalid tree JSON', 'error'); }
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
      showToast('Tree exported', 'success');
    } catch (err) { showToast(`Export error: ${err}`, 'error'); }
  };

  const handleAutoLayout = () => {
    history.save();
    const positions = computeLayout(useTreeStore.getState().nodes);
    for (const [id, pos] of Object.entries(positions)) {
      useTreeStore.getState().updateNode(id, pos);
    }
    showToast('Layout applied', 'success');
  };

  const handleZoomFit = () => {
    const nodeList = Object.values(nodes);
    if (nodeList.length === 0) return;
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (const n of nodeList) {
      minX = Math.min(minX, n.x); minY = Math.min(minY, n.y);
      maxX = Math.max(maxX, n.x + n.width); maxY = Math.max(maxY, n.y + n.height);
    }
    const pad = 80;
    const w = maxX - minX + pad * 2, h = maxY - minY + pad * 2;
    const z = Math.min(window.innerWidth / w, window.innerHeight / h, 2);
    ui.setZoom(z);
    ui.setPan(-minX * z + pad * z, -minY * z + pad * z);
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 2,
      height: 'var(--toolbar-h)', padding: '0 10px',
      background: 'linear-gradient(180deg, var(--surface-2) 0%, var(--surface-1) 100%)',
      borderBottom: '1px solid var(--border-0)', fontSize: 'var(--fs-sm)',
    }}>
      <div style={{ fontWeight: 700, fontSize: 'var(--fs-lg)', marginRight: 6, color: 'var(--accent)', letterSpacing: '-0.3px' }}>
        🌳 TalkingTrees
      </div>

      <Sep />
      <Grp>
        <Btn onClick={handleNew} tip="New Tree (Ctrl+N)">📄 New</Btn>
        <Btn onClick={handleImport} tip="Import JSON">📂 Open</Btn>
        <Btn onClick={handleExport} tip="Export JSON">💾 Save</Btn>
      </Grp>

      <Sep />
      <Grp>
        <Btn onClick={history.undo} tip="Undo (Ctrl+Z)" disabled={!history.canUndo}>↩</Btn>
        <Btn onClick={history.redo} tip="Redo (Ctrl+Shift+Z)" disabled={!history.canRedo}>↪</Btn>
      </Grp>

      <Sep />
      <Grp>
        <Btn onClick={handleAutoLayout} tip="Auto Layout (Ctrl+L)">⊞ Layout</Btn>
        <Btn onClick={handleZoomFit} tip="Zoom to Fit (Ctrl+0)">⊡ Fit</Btn>
      </Grp>

      <Sep />
      <Grp>
        <Btn onClick={() => ui.togglePanel('palette')} tip="Toggle palette" on={ui.showPalette}>◧</Btn>
        <Btn onClick={() => ui.togglePanel('properties')} tip="Toggle properties" on={ui.showProperties}>⚙</Btn>
        <Btn onClick={() => ui.togglePanel('grid')} tip="Grid (Ctrl+G)" on={ui.showGrid}>▦</Btn>
        <Btn onClick={() => ui.togglePanel('dataflow')} tip="BB flow" on={ui.showDataflow}>⇢</Btn>
        <Btn onClick={() => ui.togglePanel('minimap')} tip="Minimap" on={ui.showMinimap}>◰</Btn>
        <Btn onClick={() => ui.togglePanel('timeline')} tip="Timeline" on={ui.showTimeline}>▬</Btn>
      </Grp>

      <Sep />
      <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-validation'))} tip="Validate (Ctrl+Shift+V)">✓ Validate</Btn>
      <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-blackboard'))} tip="Blackboard Inspector">📋 BB</Btn>
      <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-shortcuts'))} tip="Shortcuts (F1)">⌨</Btn>

      <Sep />
      <Btn onClick={ui.toggleTheme} tip="Theme (Ctrl+Shift+T)">{ui.theme === 'dark' ? '☀' : '🌙'}</Btn>

      <div style={{ flex: 1 }} />

      <Grp>
        <Btn onClick={() => ui.setZoom(ui.zoom * 0.85)}>−</Btn>
        <span style={{ color: 'var(--text-2)', fontFamily: 'var(--font-mono)', fontSize: 'var(--fs-xs)', width: 36, textAlign: 'center', display: 'inline-block' }}>
          {Math.round(ui.zoom * 100)}%
        </span>
        <Btn onClick={() => ui.setZoom(ui.zoom * 1.15)}>+</Btn>
      </Grp>

      <Sep />
      <span style={{ color: 'var(--text-2)', fontSize: 'var(--fs-xs)', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{treeName}</span>
    </div>
  );
}

function Grp({ children }: { children: React.ReactNode }) { return <div style={{ display: 'flex', gap: 1 }}>{children}</div>; }
function Sep() { return <div style={{ width: 1, height: 18, background: 'var(--border-0)', margin: '0 5px' }} />; }
function Btn({ children, onClick, tip, on, disabled }: { children: React.ReactNode; onClick: () => void; tip?: string; on?: boolean; disabled?: boolean }) {
  return (
    <button onClick={onClick} title={tip} disabled={disabled} style={{
      background: on ? 'var(--accent-dim)' : undefined,
      color: on ? 'var(--accent)' : undefined,
      opacity: disabled ? 0.4 : 1,
    }}>
      {children}
    </button>
  );
}
