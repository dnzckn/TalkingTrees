/** Undo/redo history for tree state. */
import { create } from 'zustand';
import { useTreeStore } from './treeStore';
import type { CanvasNode } from '../types/tree';

interface Snapshot {
  nodes: Record<string, CanvasNode>;
  treeName: string;
}

interface HistoryState {
  past: Snapshot[];
  future: Snapshot[];
  save: () => void;
  undo: () => void;
  redo: () => void;
  canUndo: boolean;
  canRedo: boolean;
}

const MAX_HISTORY = 50;

function takeSnapshot(): Snapshot {
  const s = useTreeStore.getState();
  return {
    nodes: JSON.parse(JSON.stringify(s.nodes)),
    treeName: s.treeName,
  };
}

function restoreSnapshot(snap: Snapshot) {
  // Rebuild nodes with proper structure (JSON parse loses Set)
  useTreeStore.setState({
    nodes: snap.nodes,
    treeName: snap.treeName,
    selectedIds: new Set(),
    isDirty: true,
  });
}

export const useHistoryStore = create<HistoryState>((set, get) => ({
  past: [],
  future: [],
  canUndo: false,
  canRedo: false,

  save: () => set(s => {
    const snap = takeSnapshot();
    const past = [...s.past, snap].slice(-MAX_HISTORY);
    return { past, future: [], canUndo: past.length > 0, canRedo: false };
  }),

  undo: () => {
    const s = get();
    if (s.past.length === 0) return;
    const current = takeSnapshot();
    const prev = s.past[s.past.length - 1];
    restoreSnapshot(prev);
    set({
      past: s.past.slice(0, -1),
      future: [...s.future, current],
      canUndo: s.past.length > 1,
      canRedo: true,
    });
  },

  redo: () => {
    const s = get();
    if (s.future.length === 0) return;
    const current = takeSnapshot();
    const next = s.future[s.future.length - 1];
    restoreSnapshot(next);
    set({
      past: [...s.past, current],
      future: s.future.slice(0, -1),
      canUndo: true,
      canRedo: s.future.length > 1,
    });
  },
}));
