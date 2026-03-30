/** REST API client for TalkingTrees backend. */

import type { TreeDefinition } from '../types/tree';

const BASE_URL = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error ${response.status}: ${error}`);
  }
  return response.json();
}

export const api = {
  // Trees
  listTrees: () => fetchJson<Array<{ tree_id: string; display_name: string; latest_version: string }>>('/trees/'),

  getTree: (treeId: string, version?: string) =>
    fetchJson<TreeDefinition>(`/trees/${treeId}${version ? `?version=${version}` : ''}`),

  saveTree: (tree: TreeDefinition) =>
    fetchJson<{ version: string }>('/trees/', {
      method: 'POST',
      body: JSON.stringify(tree),
    }),

  // Behaviors
  listBehaviors: () => fetchJson<Array<{ node_type: string; category: string; display_name: string }>>('/behaviors/'),

  // Executions
  createExecution: (treeId: string, initialBlackboard?: Record<string, unknown>) =>
    fetchJson<{ execution_id: string }>('/executions/', {
      method: 'POST',
      body: JSON.stringify({ tree_id: treeId, initial_blackboard: initialBlackboard }),
    }),

  tickExecution: (executionId: string, count = 1, blackboardUpdates?: Record<string, unknown>) =>
    fetchJson<{ root_status: string; snapshot?: unknown }>(`/executions/${executionId}/tick`, {
      method: 'POST',
      body: JSON.stringify({ count, blackboard_updates: blackboardUpdates }),
    }),

  getSnapshot: (executionId: string) =>
    fetchJson<{ node_states: Record<string, { status: string }> }>(`/executions/${executionId}/snapshot`),

  // Health
  health: () => fetchJson<{ status: string }>('/health'),
};
