import { useUIStore } from '../../store/uiStore';
import { useTreeStore } from '../../store/treeStore';
import { useHistoryStore } from '../../store/historyStore';
import { useSimStore } from '../../store/simulationStore';
import { computeLayout } from '../../services/layout';
import { showToast } from '../Panels/Toast';

export function Toolbar() {
  const ui = useUIStore();
  const tree = useTreeStore();
  const hist = useHistoryStore();
  const sim = useSimStore();

  const doNew = () => { hist.save(); tree.clear(); showToast('New tree'); };
  const doImport = () => {
    const inp = document.createElement('input'); inp.type = 'file'; inp.accept = '.json';
    inp.onchange = async (e) => {
      const f = (e.target as HTMLInputElement).files?.[0]; if (!f) return;
      try { hist.save(); tree.loadTree(JSON.parse(await f.text())); showToast(`Loaded ${f.name}`, 'success'); }
      catch { showToast('Invalid JSON', 'error'); }
    }; inp.click();
  };
  const doExport = () => {
    try {
      const d = tree.exportTree();
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' }));
      a.download = `${tree.treeName.replace(/\s+/g, '_').toLowerCase()}.json`;
      a.click(); showToast('Exported', 'success');
    } catch (e) { showToast(`Error: ${e}`, 'error'); }
  };
  const doLayout = () => {
    hist.save();
    const p = computeLayout(tree.nodes);
    for (const [id, pos] of Object.entries(p)) tree.updateNode(id, pos);
    showToast('Layout applied');
  };
  const doFit = () => {
    const nl = Object.values(tree.nodes); if (!nl.length) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const n of nl) { x0 = Math.min(x0, n.x); y0 = Math.min(y0, n.y); x1 = Math.max(x1, n.x + n.width); y1 = Math.max(y1, n.y + n.height); }
    const p = 60, w = x1 - x0 + p * 2, h = y1 - y0 + p * 2;
    const z = Math.min(window.innerWidth / w, window.innerHeight / h, 2);
    ui.setZoom(z); ui.setPan(-x0 * z + p * z, -y0 * z + p * z);
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center',
      height: 'var(--toolbar-h)', padding: '0 8px', gap: 1,
      background: 'var(--s1)', borderBottom: '1px solid var(--b0)',
      fontSize: 'var(--fs-sm)',
    }}>
      {/* Brand */}
      <div style={{ fontWeight: 700, fontSize: 'var(--fs-xl)', color: 'var(--accent)', marginRight: 8, letterSpacing: '-0.5px', display: 'flex', alignItems: 'center', gap: 5 }}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="4" r="2.5" fill="var(--c-composite)"/><line x1="8" y1="6.5" x2="8" y2="9" stroke="var(--t2)" strokeWidth="1.5"/><circle cx="4" cy="13" r="2" fill="var(--c-action)"/><circle cx="12" cy="13" r="2" fill="var(--c-condition)"/><line x1="8" y1="9" x2="4" y2="11" stroke="var(--t2)" strokeWidth="1.2"/><line x1="8" y1="9" x2="12" y2="11" stroke="var(--t2)" strokeWidth="1.2"/></svg>
        TalkingTrees
      </div>

      <Sep />

      {/* File */}
      <Grp>
        <Btn onClick={doNew} tip="New (Ctrl+N)">New</Btn>
        <Btn onClick={doImport} tip="Open file">Open</Btn>
        <Btn onClick={doExport} tip="Save JSON">Save</Btn>
      </Grp>
      <Sep />

      {/* Edit */}
      <Grp>
        <Btn onClick={hist.undo} tip="Undo (Ctrl+Z)" off={!hist.canUndo}>↩</Btn>
        <Btn onClick={hist.redo} tip="Redo" off={!hist.canRedo}>↪</Btn>
        <Btn onClick={doLayout} tip="Auto Layout (Ctrl+L)">Layout</Btn>
        <Btn onClick={doFit} tip="Fit (Ctrl+0)">Fit</Btn>
      </Grp>
      <Sep />

      {/* Simulation */}
      <Grp>
        <Btn onClick={() => sim.running ? sim.pause() : sim.play()} tip="Space" accent={sim.running} style={{
          background: sim.running ? 'var(--running)' : 'var(--success)',
          color: '#000', fontWeight: 600, minWidth: 56,
        }}>
          {sim.running ? '⏸ Pause' : '▶ Run'}
        </Btn>
        <Btn onClick={sim.step} tip="Step (S)">Step</Btn>
        <Btn onClick={sim.reset} tip="Reset (R)">Reset</Btn>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginLeft: 2 }}>
          <input type="range" min={0.5} max={50} step={0.5} value={sim.tps}
            onChange={e => sim.setTps(parseFloat(e.target.value))}
            style={{ width: 50, accentColor: 'var(--accent)', height: 3 }}
          />
          <span style={{ fontFamily: 'var(--mono)', fontSize: 'var(--fs-2xs)', color: 'var(--t2)', width: 32 }}>{sim.tps.toFixed(1)}</span>
        </div>
      </Grp>
      <Sep />

      {/* View toggles */}
      <Grp>
        <Btn onClick={() => ui.togglePanel('palette')} tip="Palette" on={ui.showPalette}>☰</Btn>
        <Btn onClick={() => ui.togglePanel('properties')} tip="Properties" on={ui.showProperties}>⚙</Btn>
        <Btn onClick={() => ui.togglePanel('grid')} tip="Grid" on={ui.showGrid}>⊞</Btn>
        <Btn onClick={() => ui.togglePanel('dataflow')} tip="Dataflow" on={ui.showDataflow}>⇢</Btn>
        <Btn onClick={() => ui.togglePanel('minimap')} tip="Minimap" on={ui.showMinimap}>◰</Btn>
      </Grp>
      <Sep />

      {/* Tools */}
      <Grp>
        <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-validation'))} tip="Validate">Validate</Btn>
        <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-blackboard'))} tip="Blackboard">BB</Btn>
        <Btn onClick={() => window.dispatchEvent(new CustomEvent('show-command-palette'))} tip="Ctrl+Shift+P">⌘</Btn>
      </Grp>
      <Sep />

      <Btn onClick={ui.toggleTheme} tip="Toggle theme">{ui.theme === 'dark' ? '☀' : '🌙'}</Btn>

      <div style={{ flex: 1 }} />

      {/* Zoom */}
      <Grp>
        <Btn onClick={() => ui.setZoom(ui.zoom * 0.85)}>−</Btn>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 'var(--fs-2xs)', color: 'var(--t2)', width: 32, textAlign: 'center' }}>{Math.round(ui.zoom * 100)}%</span>
        <Btn onClick={() => ui.setZoom(ui.zoom * 1.15)}>+</Btn>
      </Grp>
    </div>
  );
}

function Grp({ children }: { children: React.ReactNode }) { return <div style={{ display: 'flex', gap: 1, alignItems: 'center' }}>{children}</div>; }
function Sep() { return <div style={{ width: 1, height: 16, background: 'var(--b0)', margin: '0 4px' }} />; }
function Btn({ children, onClick, tip, on, off, accent, style: extraStyle }: {
  children: React.ReactNode; onClick: () => void; tip?: string; on?: boolean; off?: boolean; accent?: boolean; style?: React.CSSProperties
}) {
  return (
    <button onClick={onClick} title={tip} disabled={off} style={{
      background: on ? 'var(--accent-soft)' : accent ? 'var(--accent)' : undefined,
      color: on ? 'var(--accent-vivid)' : undefined,
      ...extraStyle,
    }}>
      {children}
    </button>
  );
}
