/** Simulation engine — ports the legacy editor's tick/execute logic. */
import { create } from 'zustand';
import { useTreeStore } from './treeStore';
import type { CanvasNode } from '../types/tree';

type Status = 'SUCCESS' | 'FAILURE' | 'RUNNING' | 'INVALID';

interface TickRecord { tick: number; rootStatus: Status }

interface SimState {
  running: boolean;
  tick: number;
  tps: number;
  history: TickRecord[];
  blackboard: Map<string, unknown>;
  intervalId: number | null;

  play: () => void;
  pause: () => void;
  step: () => void;
  reset: () => void;
  setTps: (tps: number) => void;
}

export const useSimStore = create<SimState>((set, get) => ({
  running: false,
  tick: 0,
  tps: 1,
  history: [],
  blackboard: new Map(),
  intervalId: null,

  play: () => {
    const s = get();
    if (s.running) return;
    const id = window.setInterval(() => get().step(), 1000 / get().tps);
    set({ running: true, intervalId: id });
  },

  pause: () => {
    const s = get();
    if (s.intervalId) clearInterval(s.intervalId);
    set({ running: false, intervalId: null });
  },

  step: () => {
    const nodes = useTreeStore.getState().nodes;
    const updateNode = useTreeStore.getState().updateNode;
    const bb = new Map(get().blackboard);

    // Find root
    const nodeList = Object.values(nodes);
    const root = nodeList.find(n => !n.parentId);
    if (!root) return;

    // Execute tree
    const executeNode = (id: string): Status => {
      const node = nodes[id];
      if (!node) return 'FAILURE';

      let status: Status;

      switch (node.nodeType) {
        case 'Sequence':
          status = 'SUCCESS';
          for (const cid of node.childIds) {
            const cs = executeNode(cid);
            if (cs === 'FAILURE') { status = 'FAILURE'; break; }
            if (cs === 'RUNNING') { status = 'RUNNING'; break; }
          }
          break;

        case 'Selector':
          status = 'FAILURE';
          for (const cid of node.childIds) {
            const cs = executeNode(cid);
            if (cs === 'SUCCESS') { status = 'SUCCESS'; break; }
            if (cs === 'RUNNING') { status = 'RUNNING'; break; }
          }
          break;

        case 'Parallel': {
          let succ = 0, fail = 0;
          for (const cid of node.childIds) {
            const cs = executeNode(cid);
            if (cs === 'SUCCESS') succ++;
            if (cs === 'FAILURE') fail++;
          }
          status = succ === node.childIds.length ? 'SUCCESS' : fail > 0 ? 'FAILURE' : 'RUNNING';
          break;
        }

        case 'Success': status = 'SUCCESS'; break;
        case 'Failure': status = 'FAILURE'; break;
        case 'Running': status = 'RUNNING'; break;

        case 'Inverter':
          if (node.childIds.length > 0) {
            const cs = executeNode(node.childIds[0]);
            status = cs === 'SUCCESS' ? 'FAILURE' : cs === 'FAILURE' ? 'SUCCESS' : cs;
          } else { status = 'FAILURE'; }
          break;

        case 'SetBlackboardVariable':
          if (node.config.variable) bb.set(String(node.config.variable), node.config.value);
          status = 'SUCCESS';
          break;

        case 'CheckBlackboardVariableExists':
          status = node.config.variable && bb.has(String(node.config.variable)) ? 'SUCCESS' : 'FAILURE';
          break;

        case 'CheckBlackboardVariableValue': {
          const val = bb.get(String(node.config.variable ?? ''));
          const exp = node.config.value;
          const op = String(node.config.operator ?? '==');
          let r = false;
          switch (op) {
            case '==': r = val == exp; break;
            case '!=': r = val != exp; break;
            case '<': r = (val as number) < (exp as number); break;
            case '>': r = (val as number) > (exp as number); break;
            case '<=': r = (val as number) <= (exp as number); break;
            case '>=': r = (val as number) >= (exp as number); break;
          }
          status = r ? 'SUCCESS' : 'FAILURE';
          break;
        }

        default:
          // Decorators with one child — pass through
          if (node.childIds.length === 1) {
            status = executeNode(node.childIds[0]);
          } else if (node.childIds.length > 1) {
            // Treat unknown composites as sequence
            status = 'SUCCESS';
            for (const cid of node.childIds) {
              const cs = executeNode(cid);
              if (cs !== 'SUCCESS') { status = cs; break; }
            }
          } else {
            // Leaf with no special behavior — random for demo
            status = Math.random() > 0.3 ? 'SUCCESS' : 'FAILURE';
          }
      }

      updateNode(id, { status });
      return status;
    };

    const rootStatus = executeNode(root.id);

    set(s => ({
      tick: s.tick + 1,
      blackboard: bb,
      history: [...s.history.slice(-99), { tick: s.tick + 1, rootStatus }],
    }));
  },

  reset: () => {
    const s = get();
    if (s.intervalId) clearInterval(s.intervalId);
    // Clear all node statuses
    const nodes = useTreeStore.getState().nodes;
    const updateNode = useTreeStore.getState().updateNode;
    for (const id of Object.keys(nodes)) {
      updateNode(id, { status: undefined });
    }
    set({ running: false, intervalId: null, tick: 0, history: [], blackboard: new Map() });
  },

  setTps: (tps) => {
    const s = get();
    set({ tps });
    if (s.running && s.intervalId) {
      clearInterval(s.intervalId);
      const id = window.setInterval(() => get().step(), 1000 / tps);
      set({ intervalId: id });
    }
  },
}));
