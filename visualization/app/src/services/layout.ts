/** Auto-layout algorithm — ports the legacy editor's hierarchical tree layout. */

import type { CanvasNode } from '../types/tree';

const NODE_W = 180;
const H_SPACING = 150;
const V_SPACING = 120;
const START_X = 500;
const START_Y = 80;

interface LayoutInfo { width: number; offset: number; subtreeLeft: number }

/**
 * Compute auto-layout positions for all nodes.
 * Returns a map of node_id -> {x, y}.
 */
export function computeLayout(nodes: Record<string, CanvasNode>): Record<string, { x: number; y: number }> {
  const nodeList = Object.values(nodes);
  const roots = nodeList.filter(n => !n.parentId);
  if (roots.length === 0) return {};

  const root = roots[0];
  const layoutMap = new Map<string, LayoutInfo>();

  // Phase 1: post-order — calculate subtree widths
  function calcWidths(id: string) {
    const node = nodes[id];
    if (!node) return;

    for (const childId of node.childIds) calcWidths(childId);

    const children = node.childIds.map(cid => nodes[cid]).filter(Boolean);

    if (children.length === 0) {
      layoutMap.set(id, { width: NODE_W, offset: 0, subtreeLeft: 0 });
    } else if (children.length === 1) {
      const cl = layoutMap.get(children[0].id)!;
      layoutMap.set(id, { width: Math.max(cl.width, NODE_W), offset: cl.offset, subtreeLeft: 0 });
    } else {
      let currentX = 0;
      for (let i = 0; i < children.length; i++) {
        const cl = layoutMap.get(children[i].id)!;
        if (i === 0) {
          cl.subtreeLeft = 0;
          currentX = cl.width / 2;
        } else {
          const sl = currentX + H_SPACING + cl.width / 2;
          cl.subtreeLeft = sl;
          layoutMap.set(children[i].id, cl);
          currentX = sl + cl.width / 2;
        }
      }
      const first = layoutMap.get(children[0].id)!;
      const last = layoutMap.get(children[children.length - 1].id)!;
      const leftEdge = first.subtreeLeft - first.width / 2;
      const rightEdge = last.subtreeLeft + last.width / 2;
      const center = (leftEdge + rightEdge) / 2;
      layoutMap.set(id, { width: rightEdge - leftEdge, offset: center, subtreeLeft: 0 });
    }
  }
  calcWidths(root.id);

  // Phase 2: top-down — assign absolute positions
  const result: Record<string, { x: number; y: number }> = {};

  function assignPositions(id: string, baseX: number, y: number) {
    const node = nodes[id];
    if (!node) return;
    const layout = layoutMap.get(id)!;

    result[id] = { x: baseX - NODE_W / 2, y };

    const children = node.childIds.map(cid => nodes[cid]).filter(Boolean);
    if (children.length === 0) return;

    for (const child of children) {
      const cl = layoutMap.get(child.id)!;
      const childX = baseX + (cl.subtreeLeft - layout.offset);
      assignPositions(child.id, childX, y + V_SPACING);
    }
  }

  const rootLayout = layoutMap.get(root.id)!;
  assignPositions(root.id, START_X + rootLayout.offset, START_Y);

  return result;
}
