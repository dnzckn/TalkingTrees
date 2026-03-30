/** Complete registry of all node types for the palette.
 * Includes all built-in py_trees types plus WP1-17 additions. */

import type { NodeCategory } from '../../types/tree';

export interface NodeTypeInfo {
  type: string;
  displayName: string;
  category: NodeCategory;
  description: string;
  color: string;
  icon: string;
  defaultConfig: Record<string, unknown>;
  section: string;
}

export const NODE_REGISTRY: NodeTypeInfo[] = [
  // ── COMPOSITES ──
  { type: 'Sequence', displayName: 'Sequence', category: 'composite', description: 'Execute children in order, ALL must succeed', color: '#4ec9b0', icon: '→', defaultConfig: { memory: true }, section: 'Composites' },
  { type: 'Selector', displayName: 'Selector', category: 'composite', description: 'Try children until one succeeds', color: '#4ec9b0', icon: '?', defaultConfig: { memory: false }, section: 'Composites' },
  { type: 'Parallel', displayName: 'Parallel', category: 'composite', description: 'Execute children concurrently', color: '#4ec9b0', icon: '⫴', defaultConfig: { policy: 'SuccessOnAll' }, section: 'Composites' },

  // ── DECORATORS — Status Converters ──
  { type: 'Inverter', displayName: 'Inverter', category: 'decorator', description: 'Flip SUCCESS ⇄ FAILURE', color: '#dcdcaa', icon: '¬', defaultConfig: {}, section: 'Decorators' },
  { type: 'SuccessIsFailure', displayName: 'Success→Failure', category: 'decorator', description: 'SUCCESS → FAILURE', color: '#dcdcaa', icon: '↓', defaultConfig: {}, section: 'Decorators' },
  { type: 'FailureIsSuccess', displayName: 'Failure→Success', category: 'decorator', description: 'FAILURE → SUCCESS', color: '#dcdcaa', icon: '↑', defaultConfig: {}, section: 'Decorators' },
  { type: 'FailureIsRunning', displayName: 'Failure→Running', category: 'decorator', description: 'FAILURE → RUNNING', color: '#dcdcaa', icon: '~', defaultConfig: {}, section: 'Decorators' },
  { type: 'RunningIsFailure', displayName: 'Running→Failure', category: 'decorator', description: 'RUNNING → FAILURE', color: '#dcdcaa', icon: '↓', defaultConfig: {}, section: 'Decorators' },
  { type: 'RunningIsSuccess', displayName: 'Running→Success', category: 'decorator', description: 'RUNNING → SUCCESS', color: '#dcdcaa', icon: '↑', defaultConfig: {}, section: 'Decorators' },
  { type: 'SuccessIsRunning', displayName: 'Success→Running', category: 'decorator', description: 'SUCCESS → RUNNING', color: '#dcdcaa', icon: '~', defaultConfig: {}, section: 'Decorators' },

  // ── DECORATORS — Control ──
  { type: 'Retry', displayName: 'Retry', category: 'decorator', description: 'Retry N times on failure', color: '#dcdcaa', icon: '↻', defaultConfig: { num_failures: 3 }, section: 'Decorators' },
  { type: 'Repeat', displayName: 'Repeat', category: 'decorator', description: 'Repeat N times', color: '#dcdcaa', icon: '⟳', defaultConfig: { num_success: 3 }, section: 'Decorators' },
  { type: 'OneShot', displayName: 'OneShot', category: 'decorator', description: 'Execute once then return fixed status', color: '#dcdcaa', icon: '1', defaultConfig: {}, section: 'Decorators' },
  { type: 'Timeout', displayName: 'Timeout', category: 'decorator', description: 'Fail if child takes too long', color: '#dcdcaa', icon: '⏱', defaultConfig: { duration: 5.0 }, section: 'Decorators' },
  { type: 'EternalGuard', displayName: 'Eternal Guard', category: 'decorator', description: 'Continuous condition monitoring', color: '#dcdcaa', icon: '⛨', defaultConfig: {}, section: 'Decorators' },
  { type: 'Condition', displayName: 'Condition', category: 'decorator', description: 'Blocking conditional decorator', color: '#dcdcaa', icon: '⊳', defaultConfig: {}, section: 'Decorators' },
  { type: 'Count', displayName: 'Count', category: 'decorator', description: 'Track execution statistics', color: '#dcdcaa', icon: '#', defaultConfig: {}, section: 'Decorators' },
  { type: 'StatusToBlackboard', displayName: 'Status→BB', category: 'decorator', description: 'Write child status to blackboard', color: '#dcdcaa', icon: '📋', defaultConfig: { variable: 'status' }, section: 'Decorators' },

  // ── DECORATORS — Rate Limiting (WP-11) ──
  { type: 'RateLimiter', displayName: 'Rate Limiter', category: 'decorator', description: 'Limits child execution rate', color: '#e74c3c', icon: '⏩', defaultConfig: { max_count: 10, window_seconds: 1.0, on_limit: 'FAILURE' }, section: 'Rate Limiting' },
  { type: 'Debounce', displayName: 'Debounce', category: 'decorator', description: 'Cooldown between child ticks', color: '#f39c12', icon: '⏸', defaultConfig: { cooldown_seconds: 1.0, on_cooldown: 'RUNNING' }, section: 'Rate Limiting' },
  { type: 'WindowedAggregator', displayName: 'Windowed Aggregator', category: 'decorator', description: 'Requires N successes in time window', color: '#3498db', icon: '📊', defaultConfig: { window_seconds: 10.0, min_successes: 3 }, section: 'Rate Limiting' },

  // ── ACTIONS — Basic Status ──
  { type: 'Success', displayName: 'Success', category: 'action', description: 'Always return SUCCESS', color: '#4fc1ff', icon: '✓', defaultConfig: {}, section: 'Actions' },
  { type: 'Failure', displayName: 'Failure', category: 'action', description: 'Always return FAILURE', color: '#4fc1ff', icon: '✗', defaultConfig: {}, section: 'Actions' },
  { type: 'Running', displayName: 'Running', category: 'action', description: 'Always return RUNNING', color: '#4fc1ff', icon: '~', defaultConfig: {}, section: 'Actions' },
  { type: 'Dummy', displayName: 'Dummy', category: 'action', description: 'Crash test dummy', color: '#4fc1ff', icon: '💥', defaultConfig: {}, section: 'Actions' },

  // ── ACTIONS — Time-Based ──
  { type: 'TickCounter', displayName: 'Tick Counter', category: 'action', description: 'Count N ticks before completing', color: '#4fc1ff', icon: '🔢', defaultConfig: { duration: 5 }, section: 'Actions' },
  { type: 'SuccessEveryN', displayName: 'Success Every N', category: 'action', description: 'Return SUCCESS every N ticks', color: '#4fc1ff', icon: '🔄', defaultConfig: { n: 5 }, section: 'Actions' },
  { type: 'Periodic', displayName: 'Periodic', category: 'action', description: 'Cycle through statuses', color: '#4fc1ff', icon: '📡', defaultConfig: { n: 3 }, section: 'Actions' },
  { type: 'StatusQueue', displayName: 'Status Queue', category: 'action', description: 'Predefined status queue', color: '#4fc1ff', icon: '📋', defaultConfig: { queue: ['SUCCESS'] }, section: 'Actions' },

  // ── ACTIONS — Blackboard ──
  { type: 'SetBlackboardVariable', displayName: 'Set BB Variable', category: 'action', description: 'Write value to blackboard', color: '#4fc1ff', icon: '✏', defaultConfig: { variable: '', value: '' }, section: 'Blackboard' },
  { type: 'UnsetBlackboardVariable', displayName: 'Unset BB Variable', category: 'action', description: 'Remove blackboard variable', color: '#4fc1ff', icon: '🗑', defaultConfig: { variable: '' }, section: 'Blackboard' },
  { type: 'BlackboardToStatus', displayName: 'BB→Status', category: 'action', description: 'Return status from blackboard value', color: '#4fc1ff', icon: '📤', defaultConfig: { variable: '' }, section: 'Blackboard' },

  // ── CONDITIONS ──
  { type: 'CheckBlackboardVariableExists', displayName: 'BB Key Exists?', category: 'condition', description: 'Check if blackboard key exists', color: '#c586c0', icon: '?', defaultConfig: { variable: '' }, section: 'Conditions' },
  { type: 'CheckBlackboardVariableValue', displayName: 'BB Value Check', category: 'condition', description: 'Check blackboard value with operator', color: '#c586c0', icon: '⚖', defaultConfig: { variable: '', operator: '==', value: '' }, section: 'Conditions' },
  { type: 'CheckBlackboardVariableValues', displayName: 'BB Multi Check', category: 'condition', description: 'Check multiple BB conditions', color: '#c586c0', icon: '⚖⚖', defaultConfig: { checks: [] }, section: 'Conditions' },
  { type: 'WaitForBlackboardVariable', displayName: 'Wait for BB Key', category: 'condition', description: 'Block until key exists', color: '#c586c0', icon: '⏳', defaultConfig: { variable: '' }, section: 'Conditions' },
  { type: 'WaitForBlackboardVariableValue', displayName: 'Wait for BB Value', category: 'condition', description: 'Block until value matches', color: '#c586c0', icon: '⏳', defaultConfig: { variable: '', operator: '==', value: '' }, section: 'Conditions' },

  // ── SPECIAL — Subtree Refs (WP-1) ──
  { type: 'SubTreeRef', displayName: 'Subtree Reference', category: 'custom', description: 'Reference to external subtree (file or ID)', color: '#9b59b6', icon: '🔗', defaultConfig: { tree_file: '', tree_id: '' }, section: 'References' },

  // ── SPECIAL — Async (WP-8) ──
  { type: 'AsyncAction', displayName: 'Async Action', category: 'action', description: 'Non-blocking async callable execution', color: '#e67e22', icon: '⚡', defaultConfig: { callable: '', timeout_ms: 5000, on_timeout: 'FAILURE', output_key: '' }, section: 'Async & Remote' },

  // ── SPECIAL — Remote (WP-5) ──
  { type: 'RemoteSubtree', displayName: 'Remote Subtree', category: 'custom', description: 'Proxy execution to remote endpoint', color: '#9b59b6', icon: '☁', defaultConfig: { endpoint: '', timeout_ms: 5000 }, section: 'Async & Remote' },

  // ── SPECIAL — Resources (WP-13) ──
  { type: 'AcquireResource', displayName: 'Acquire Resource', category: 'action', description: 'Acquire a shared resource', color: '#27ae60', icon: '🔒', defaultConfig: { resource_id: '', timeout_ms: 0, on_unavailable: 'FAILURE' }, section: 'Resources' },
  { type: 'ReleaseResource', displayName: 'Release Resource', category: 'action', description: 'Release a shared resource', color: '#27ae60', icon: '🔓', defaultConfig: { resource_id: '' }, section: 'Resources' },
];

/** Group nodes by section for palette rendering. */
export function getNodesBySection(): Record<string, NodeTypeInfo[]> {
  const sections: Record<string, NodeTypeInfo[]> = {};
  for (const node of NODE_REGISTRY) {
    if (!sections[node.section]) sections[node.section] = [];
    sections[node.section].push(node);
  }
  return sections;
}

/** Find a node type by its type string. */
export function getNodeTypeInfo(type: string): NodeTypeInfo | undefined {
  return NODE_REGISTRY.find((n) => n.type === type);
}
