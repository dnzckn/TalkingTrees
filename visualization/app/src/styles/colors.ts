/** Node category colors for canvas rendering. */

import type { NodeCategory } from '../types/tree';

export const categoryColors: Record<NodeCategory, string> = {
  composite: '#4ec9b0',
  decorator: '#dcdcaa',
  action: '#4fc1ff',
  condition: '#c586c0',
  custom: '#ce9178',
};

export const statusColors = {
  SUCCESS: '#4caf50',
  FAILURE: '#f44336',
  RUNNING: '#ffc107',
  INVALID: '#858585',
} as const;

/** Special node type colors override category defaults. */
export const nodeTypeColors: Record<string, string> = {
  SubTreeRef: '#9b59b6',
  AsyncAction: '#e67e22',
  RemoteSubtree: '#9b59b6',
  RateLimiter: '#e74c3c',
  Debounce: '#f39c12',
  WindowedAggregator: '#3498db',
  AcquireResource: '#27ae60',
  ReleaseResource: '#27ae60',
};

export function getNodeColor(nodeType: string, category: NodeCategory): string {
  return nodeTypeColors[nodeType] || categoryColors[category] || categoryColors.action;
}
