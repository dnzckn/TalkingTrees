import { useMemo } from 'react';
import { useTreeStore } from '../../store/treeStore';

interface Issue { level: 'error' | 'warning' | 'info'; msg: string; nodeId?: string }

export function ValidationPanel({ onClose }: { onClose: () => void }) {
  const nodes = useTreeStore(s => s.nodes);

  const issues = useMemo(() => {
    const out: Issue[] = [];
    const nodeList = Object.values(nodes);
    const roots = nodeList.filter(n => !n.parentId);

    if (nodeList.length === 0) { out.push({ level: 'info', msg: 'Tree is empty' }); return out; }
    if (roots.length === 0) out.push({ level: 'error', msg: 'No root node found' });
    if (roots.length > 1) out.push({ level: 'error', msg: `Multiple root nodes found (${roots.length})` });

    for (const n of nodeList) {
      // Decorators must have exactly 1 child
      const info = n.nodeType;
      if (['Inverter', 'Retry', 'Repeat', 'Timeout', 'OneShot', 'EternalGuard', 'Condition', 'Count',
        'StatusToBlackboard', 'SuccessIsFailure', 'FailureIsSuccess', 'FailureIsRunning',
        'RunningIsFailure', 'RunningIsSuccess', 'SuccessIsRunning', 'RateLimiter', 'Debounce', 'WindowedAggregator'].includes(info)) {
        if (n.childIds.length !== 1) out.push({ level: 'error', msg: `Decorator "${n.name}" must have exactly 1 child (has ${n.childIds.length})`, nodeId: n.id });
      }
      // Composites need children
      if (['Sequence', 'Selector', 'Parallel'].includes(info) && n.childIds.length === 0) {
        out.push({ level: 'warning', msg: `Composite "${n.name}" has no children`, nodeId: n.id });
      }
      // Actions shouldn't have children
      if (['Success', 'Failure', 'Running', 'Dummy', 'SetBlackboardVariable', 'UnsetBlackboardVariable',
        'CheckBlackboardVariableExists', 'CheckBlackboardVariableValue', 'AsyncAction', 'RemoteSubtree',
        'AcquireResource', 'ReleaseResource', 'SubTreeRef'].includes(info) && n.childIds.length > 0) {
        out.push({ level: 'warning', msg: `Leaf node "${n.name}" should not have children`, nodeId: n.id });
      }
      // Orphaned nodes
      if (!n.parentId && !roots.includes(n)) {
        out.push({ level: 'warning', msg: `Orphaned node "${n.name}"`, nodeId: n.id });
      }
    }

    if (out.length === 0) out.push({ level: 'info', msg: `Tree is valid (${nodeList.length} nodes)` });
    return out;
  }, [nodes]);

  const errors = issues.filter(i => i.level === 'error').length;
  const warnings = issues.filter(i => i.level === 'warning').length;

  const ICONS = { error: '✕', warning: '⚠', info: 'ℹ' };
  const COLORS = { error: 'var(--status-failure)', warning: 'var(--status-running)', info: 'var(--accent)' };

  return (
    <div style={{
      position: 'absolute', bottom: 50, left: '50%', transform: 'translateX(-50%)',
      width: 440, maxHeight: 260, background: 'var(--surface-2)', border: '1px solid var(--border-1)',
      borderRadius: 'var(--r-md)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)', zIndex: 100,
      display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 12px', borderBottom: '1px solid var(--border-0)',
        fontWeight: 600, fontSize: 'var(--fs-sm)',
      }}>
        <span>Validation {errors > 0 ? `— ${errors} error(s)` : warnings > 0 ? `— ${warnings} warning(s)` : '— OK'}</span>
        <button onClick={onClose} style={{ background: 'transparent', padding: '2px 6px' }}>✕</button>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: '4px 0' }}>
        {issues.map((issue, i) => (
          <div key={i} style={{
            display: 'flex', alignItems: 'start', gap: 8, padding: '5px 12px',
            fontSize: 'var(--fs-sm)', cursor: issue.nodeId ? 'pointer' : 'default',
          }}
            onClick={() => { if (issue.nodeId) useTreeStore.getState().selectNode(issue.nodeId, false); }}
          >
            <span style={{ color: COLORS[issue.level], fontWeight: 700, flexShrink: 0 }}>{ICONS[issue.level]}</span>
            <span style={{ color: 'var(--text-1)' }}>{issue.msg}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
