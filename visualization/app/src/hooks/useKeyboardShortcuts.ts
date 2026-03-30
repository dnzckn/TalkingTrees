import { useEffect } from 'react';
import { useTreeStore } from '../store/treeStore';
import { useUIStore } from '../store/uiStore';
import { useSimStore } from '../store/simulationStore';
import { useHistoryStore } from '../store/historyStore';
import { computeLayout } from '../services/layout';

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const ctrl = e.ctrlKey || e.metaKey;
      const shift = e.shiftKey;
      const key = e.key.toLowerCase();
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      // ── Simulation ──
      if (key === ' ' && !ctrl) { e.preventDefault(); const s = useSimStore.getState(); s.running ? s.pause() : s.play(); }
      if (key === 's' && !ctrl) { e.preventDefault(); useSimStore.getState().step(); }
      if (key === 'r' && !ctrl) { e.preventDefault(); useSimStore.getState().reset(); }

      // ── Undo/Redo ──
      if (ctrl && key === 'z' && !shift) { e.preventDefault(); useHistoryStore.getState().undo(); }
      if (ctrl && shift && key === 'z') { e.preventDefault(); useHistoryStore.getState().redo(); }
      if (ctrl && key === 'y') { e.preventDefault(); useHistoryStore.getState().redo(); }

      // ── Delete ──
      if (key === 'delete' || key === 'backspace') {
        e.preventDefault();
        useHistoryStore.getState().save();
        for (const id of useTreeStore.getState().selectedIds) useTreeStore.getState().deleteNode(id);
      }

      // ── Select all ──
      if (ctrl && key === 'a') {
        e.preventDefault();
        const s = useTreeStore.getState();
        for (const id of Object.keys(s.nodes)) s.selectNode(id, true);
      }

      // ── New ──
      if (ctrl && key === 'n') { e.preventDefault(); useHistoryStore.getState().save(); useTreeStore.getState().clear(); }

      // ── Auto layout ──
      if (ctrl && key === 'l') {
        e.preventDefault();
        useHistoryStore.getState().save();
        const positions = computeLayout(useTreeStore.getState().nodes);
        for (const [id, pos] of Object.entries(positions)) useTreeStore.getState().updateNode(id, pos);
      }

      // ── View ──
      if (ctrl && key === 'g') { e.preventDefault(); useUIStore.getState().togglePanel('grid'); }
      if (ctrl && shift && key === 't') { e.preventDefault(); useUIStore.getState().toggleTheme(); }
      if (ctrl && shift && key === 'd') { e.preventDefault(); useUIStore.getState().togglePanel('dataflow'); }
      if (ctrl && shift && key === 'v') { e.preventDefault(); window.dispatchEvent(new CustomEvent('show-validation')); }
      if (key === '+' || key === '=') { e.preventDefault(); useUIStore.getState().setZoom(useUIStore.getState().zoom * 1.1); }
      if (key === '-') { e.preventDefault(); useUIStore.getState().setZoom(useUIStore.getState().zoom * 0.9); }
      if (ctrl && key === '0') { e.preventDefault(); useUIStore.getState().setZoom(1); useUIStore.getState().setPan(0, 0); }

      // ── Collapse ──
      if (key === 'c' && !ctrl) {
        const sel = [...useTreeStore.getState().selectedIds][0];
        if (sel) {
          const n = useTreeStore.getState().nodes[sel];
          if (n) useTreeStore.getState().updateNode(sel, { collapsed: !n.collapsed });
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);
}
