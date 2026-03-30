import { useEffect, useCallback, useRef, useState } from 'react';
import { Toolbar } from './components/Toolbar/Toolbar';
import { Palette } from './components/Palette/Palette';
import { TreeCanvas } from './components/Canvas/TreeCanvas';
import { PropertiesPanel } from './components/Properties/PropertiesPanel';
import { StatusBar } from './components/StatusBar/StatusBar';
import { ContextMenu } from './components/ContextMenu';
import { Timeline } from './components/Timeline';
import { useUIStore } from './store/uiStore';
import { useTreeStore } from './store/treeStore';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import './styles/global.css';

export default function App() {
  const { showPalette, showProperties, showTimeline } = useUIStore();
  useKeyboardShortcuts();

  // Load example tree on first mount
  useEffect(() => {
    const nodes = useTreeStore.getState().nodes;
    if (Object.keys(nodes).length === 0) {
      // Create a simple example tree
      const store = useTreeStore.getState();
      const rootId = store.addNode({ nodeType: 'Sequence', name: 'Root', x: 400, y: 60, config: { memory: true } });
      const c1 = store.addNode({ nodeType: 'CheckBlackboardVariableValue', name: 'Check Battery', x: 200, y: 200, config: { variable: 'battery', operator: '>', value: 20 } });
      const c2 = store.addNode({ nodeType: 'Selector', name: 'Choose Action', x: 500, y: 200, config: { memory: false } });
      const c3 = store.addNode({ nodeType: 'Success', name: 'Patrol', x: 400, y: 360 });
      const c4 = store.addNode({ nodeType: 'SetBlackboardVariable', name: 'Set Mode', x: 600, y: 360, config: { variable: 'mode', value: 'active' } });
      store.setParent(c1, rootId);
      store.setParent(c2, rootId);
      store.setParent(c3, c2);
      store.setParent(c4, c2);
    }
  }, []);

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `${showPalette ? 'var(--sidebar-w)' : '0px'} 1fr ${showProperties ? 'var(--props-w)' : '0px'}`,
      gridTemplateRows: `var(--toolbar-h) 1fr ${showTimeline ? 'var(--timeline-h)' : '0px'} var(--statusbar-h)`,
      height: '100vh',
      width: '100vw',
      overflow: 'hidden',
      background: 'var(--surface-0)',
    }}>
      {/* Toolbar */}
      <header style={{ gridColumn: '1 / -1' }}>
        <Toolbar />
      </header>

      {/* Palette */}
      {showPalette && (
        <aside style={{
          background: 'var(--surface-1)',
          borderRight: '1px solid var(--border-0)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <Palette />
        </aside>
      )}

      {/* Canvas */}
      <main style={{ overflow: 'hidden', position: 'relative' }}>
        <TreeCanvas />
        <ContextMenu />
      </main>

      {/* Properties */}
      {showProperties && (
        <aside style={{
          background: 'var(--surface-1)',
          borderLeft: '1px solid var(--border-0)',
          overflow: 'auto',
        }}>
          <PropertiesPanel />
        </aside>
      )}

      {/* Timeline */}
      {showTimeline && (
        <div style={{ gridColumn: '1 / -1', borderTop: '1px solid var(--border-0)' }}>
          <Timeline />
        </div>
      )}

      {/* Status Bar */}
      <footer style={{ gridColumn: '1 / -1' }}>
        <StatusBar />
      </footer>
    </div>
  );
}
