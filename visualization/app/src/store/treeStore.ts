import { create } from 'zustand';
import type { CanvasNode, TreeDefinition } from '../types/tree';

// Simple UUID generator (no dep needed)
function genId(): string {
  return crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

interface TreeState {
  nodes: Record<string, CanvasNode>;
  selectedIds: Set<string>;
  treeName: string;
  treeVersion: string;
  treeId: string;
  isDirty: boolean;

  // Actions
  addNode: (node: Partial<CanvasNode> & { nodeType: string; name: string }) => string;
  updateNode: (id: string, updates: Partial<CanvasNode>) => void;
  deleteNode: (id: string) => void;
  selectNode: (id: string, multi?: boolean) => void;
  clearSelection: () => void;
  setParent: (childId: string, parentId: string | null) => void;
  loadTree: (def: TreeDefinition) => void;
  exportTree: () => TreeDefinition;
  clear: () => void;
}

export const useTreeStore = create<TreeState>((set, get) => ({
  nodes: {},
  selectedIds: new Set<string>(),
  treeName: 'Untitled Tree',
  treeVersion: '1.0.0',
  treeId: genId(),
  isDirty: false,

  addNode: (partial) => {
    const id = partial.id || genId();
    const node: CanvasNode = {
      id,
      nodeType: partial.nodeType,
      name: partial.name,
      config: partial.config || {},
      description: partial.description,
      parentId: partial.parentId ?? null,
      childIds: partial.childIds || [],
      x: partial.x ?? 100,
      y: partial.y ?? 100,
      width: 180,
      height: 70,
      collapsed: false,
      macro: partial.macro,
      blackboardInput: partial.blackboardInput,
      blackboardOutput: partial.blackboardOutput,
      treeFile: partial.treeFile,
      treeId: partial.treeId,
      ref: partial.ref,
    };
    set((s) => ({
      nodes: { ...s.nodes, [id]: node },
      isDirty: true,
    }));
    return id;
  },

  updateNode: (id, updates) => set((s) => {
    const existing = s.nodes[id];
    if (!existing) return s;
    return {
      nodes: { ...s.nodes, [id]: { ...existing, ...updates } },
      isDirty: true,
    };
  }),

  deleteNode: (id) => set((s) => {
    const node = s.nodes[id];
    if (!node) return s;
    const newNodes = { ...s.nodes };
    // Remove from parent's childIds
    if (node.parentId && newNodes[node.parentId]) {
      newNodes[node.parentId] = {
        ...newNodes[node.parentId],
        childIds: newNodes[node.parentId].childIds.filter((c) => c !== id),
      };
    }
    // Delete all descendants recursively
    const toDelete = [id];
    while (toDelete.length > 0) {
      const did = toDelete.pop()!;
      const dnode = newNodes[did];
      if (dnode) {
        toDelete.push(...dnode.childIds);
        delete newNodes[did];
      }
    }
    const newSelected = new Set(s.selectedIds);
    newSelected.delete(id);
    return { nodes: newNodes, selectedIds: newSelected, isDirty: true };
  }),

  selectNode: (id, multi) => set((s) => {
    if (multi) {
      const next = new Set(s.selectedIds);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return { selectedIds: next };
    }
    return { selectedIds: new Set([id]) };
  }),

  clearSelection: () => set({ selectedIds: new Set() }),

  setParent: (childId, parentId) => set((s) => {
    const child = s.nodes[childId];
    if (!child) return s;
    const newNodes = { ...s.nodes };
    // Remove from old parent
    if (child.parentId && newNodes[child.parentId]) {
      newNodes[child.parentId] = {
        ...newNodes[child.parentId],
        childIds: newNodes[child.parentId].childIds.filter((c) => c !== childId),
      };
    }
    // Add to new parent
    if (parentId && newNodes[parentId]) {
      newNodes[parentId] = {
        ...newNodes[parentId],
        childIds: [...newNodes[parentId].childIds, childId],
      };
    }
    newNodes[childId] = { ...child, parentId };
    return { nodes: newNodes, isDirty: true };
  }),

  loadTree: (def) => {
    const nodes: Record<string, CanvasNode> = {};
    let yCounter = 0;

    function walk(nodeDef: import('../types/tree').TreeNodeDefinition, parentId: string | null, depth: number) {
      const id = nodeDef.node_id || genId();
      nodes[id] = {
        id,
        nodeType: nodeDef.node_type,
        name: nodeDef.name,
        config: nodeDef.config || {},
        description: nodeDef.description,
        parentId,
        childIds: [],
        x: depth * 220 + 50,
        y: yCounter * 100 + 50,
        width: 180,
        height: 70,
        collapsed: false,
        macro: nodeDef.macro,
        blackboardInput: nodeDef.blackboard_input,
        blackboardOutput: nodeDef.blackboard_output,
        treeFile: nodeDef.tree_file,
        treeId: nodeDef.tree_id,
        ref: nodeDef.$ref,
      };
      if (parentId && nodes[parentId]) {
        nodes[parentId].childIds.push(id);
      }
      yCounter++;
      for (const child of nodeDef.children || []) {
        walk(child, id, depth + 1);
      }
    }

    walk(def.root, null, 0);
    set({
      nodes,
      treeName: def.metadata.name,
      treeVersion: def.metadata.version,
      treeId: def.tree_id,
      selectedIds: new Set(),
      isDirty: false,
    });
  },

  exportTree: () => {
    const state = get();
    // Find root (node with no parent)
    const rootId = Object.values(state.nodes).find((n) => !n.parentId)?.id;
    if (!rootId) throw new Error('No root node found');

    function buildNodeDef(id: string): import('../types/tree').TreeNodeDefinition {
      const node = state.nodes[id];
      return {
        node_type: node.nodeType,
        node_id: node.id,
        name: node.name,
        config: node.config,
        description: node.description,
        children: node.childIds.map(buildNodeDef),
        $ref: node.ref,
        tree_id: node.treeId,
        tree_file: node.treeFile,
        blackboard_input: node.blackboardInput,
        blackboard_output: node.blackboardOutput,
        macro: node.macro,
      };
    }

    return {
      $schema: '1.0.0',
      tree_id: state.treeId,
      metadata: {
        name: state.treeName,
        version: state.treeVersion,
        tags: [],
        status: 'draft' as const,
      },
      root: buildNodeDef(rootId),
      subtrees: {},
    };
  },

  clear: () => set({
    nodes: {},
    selectedIds: new Set(),
    treeName: 'Untitled Tree',
    treeVersion: '1.0.0',
    treeId: genId(),
    isDirty: false,
  }),
}));
