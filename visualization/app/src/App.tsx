import { useEffect, useState } from 'react';
import { Toolbar } from './components/Toolbar/Toolbar';
import { Palette } from './components/Palette/Palette';
import { TreeCanvas } from './components/Canvas/TreeCanvas';
import { PropertiesPanel } from './components/Properties/PropertiesPanel';
import { StatusBar } from './components/StatusBar/StatusBar';
import { ContextMenu } from './components/ContextMenu';
import { Timeline } from './components/Timeline';
import { ToastContainer } from './components/Panels/Toast';
import { Minimap } from './components/Panels/Minimap';
import { BlackboardInspector } from './components/Panels/BlackboardInspector';
import { ValidationPanel } from './components/Panels/ValidationPanel';
import { ShortcutsModal } from './components/Modals/ShortcutsModal';
import { useUIStore } from './store/uiStore';
import { useTreeStore } from './store/treeStore';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import './styles/global.css';

export default function App() {
  const { showPalette, showProperties, showTimeline, showMinimap } = useUIStore();
  const [showBB, setShowBB] = useState(false);
  const [showValidation, setShowValidation] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);

  useKeyboardShortcuts();

  // Panel event listeners
  useEffect(() => {
    const onBB = () => setShowBB(v => !v);
    const onVal = () => setShowValidation(v => !v);
    const onSC = () => setShowShortcuts(v => !v);
    const onF1 = (e: KeyboardEvent) => { if (e.key === 'F1') { e.preventDefault(); setShowShortcuts(v => !v); } };
    window.addEventListener('show-blackboard', onBB);
    window.addEventListener('show-validation', onVal);
    window.addEventListener('show-shortcuts', onSC);
    window.addEventListener('keydown', onF1);
    return () => {
      window.removeEventListener('show-blackboard', onBB);
      window.removeEventListener('show-validation', onVal);
      window.removeEventListener('show-shortcuts', onSC);
      window.removeEventListener('keydown', onF1);
    };
  }, []);

  // Load example tree on first mount
  useEffect(() => {
    if (Object.keys(useTreeStore.getState().nodes).length > 0) return;
    const store = useTreeStore.getState();
    const r = store.addNode({ nodeType: 'Sequence', name: 'Root', x: 400, y: 60, config: { memory: true } });
    const c1 = store.addNode({ nodeType: 'CheckBlackboardVariableValue', name: 'Check Battery', x: 200, y: 200, config: { variable: 'battery', operator: '>', value: 20 } });
    const c2 = store.addNode({ nodeType: 'Selector', name: 'Choose Action', x: 500, y: 200, config: { memory: false } });
    const c3 = store.addNode({ nodeType: 'SetBlackboardVariable', name: 'Set Patrol', x: 350, y: 360, config: { variable: 'mode', value: 'patrol' } });
    const c4 = store.addNode({ nodeType: 'Success', name: 'Idle', x: 550, y: 360 });
    store.setParent(c1, r); store.setParent(c2, r);
    store.setParent(c3, c2); store.setParent(c4, c2);
  }, []);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `${showPalette ? 'var(--sidebar-w)' : '0px'} 1fr ${showProperties ? 'var(--props-w)' : '0px'}`,
      gridTemplateRows: `var(--toolbar-h) 1fr ${showTimeline ? 'var(--timeline-h)' : '0px'} var(--statusbar-h)`,
      height: '100vh', width: '100vw', overflow: 'hidden', background: 'var(--surface-0)',
    }}>
      <header style={{ gridColumn: '1 / -1' }}><Toolbar /></header>

      {showPalette && (
        <aside style={{ background: 'var(--surface-1)', borderRight: '1px solid var(--border-0)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <Palette />
        </aside>
      )}

      <main style={{ overflow: 'hidden', position: 'relative' }}>
        <TreeCanvas />
        <ContextMenu />
        {showMinimap && <Minimap />}
        {showBB && <BlackboardInspector onClose={() => setShowBB(false)} />}
        {showValidation && <ValidationPanel onClose={() => setShowValidation(false)} />}
      </main>

      {showProperties && (
        <aside style={{ background: 'var(--surface-1)', borderLeft: '1px solid var(--border-0)', overflow: 'auto' }}>
          <PropertiesPanel />
        </aside>
      )}

      {showTimeline && (
        <div style={{ gridColumn: '1 / -1', borderTop: '1px solid var(--border-0)' }}>
          <Timeline />
        </div>
      )}

      <footer style={{ gridColumn: '1 / -1' }}><StatusBar /></footer>

      {/* Overlays */}
      <ToastContainer />
      {showShortcuts && <ShortcutsModal onClose={() => setShowShortcuts(false)} />}
    </div>
  );
}
