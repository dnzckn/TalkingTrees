import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';
import { useSimStore } from '../../store/simulationStore';

export function StatusBar() {
  const { nodes, selectedIds, treeName, isDirty } = useTreeStore();
  const { zoom } = useUIStore();
  const { running, tick } = useSimStore();

  const nodeCount = Object.keys(nodes).length;
  const connCount = Object.values(nodes).reduce((s, n) => s + n.childIds.length, 0);
  const selCount = selectedIds.size;

  // Breadcrumb for selected node
  let breadcrumb = '';
  const selId = [...selectedIds][0];
  if (selId) {
    const parts: string[] = [];
    let cur: string | null = selId;
    while (cur && nodes[cur]) {
      parts.unshift(nodes[cur].name);
      cur = nodes[cur].parentId;
    }
    breadcrumb = parts.join(' > ');
  }

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 12,
      height: 'var(--statusbar-h)', padding: '0 12px',
      background: 'var(--surface-2)', borderTop: '1px solid var(--border-0)',
      fontSize: 'var(--fs-xs)', color: 'var(--text-2)',
    }}>
      {/* Status indicator */}
      <div style={{
        width: 8, height: 8, borderRadius: '50%',
        background: running ? 'var(--status-running)' : isDirty ? 'var(--accent)' : 'var(--status-success)',
      }} />

      <span style={{ color: 'var(--text-1)' }}>{treeName}</span>

      <Sep />
      <span>Nodes: {nodeCount}</span>
      <span>Connections: {connCount}</span>
      {selCount > 0 && <span>Selected: {selCount}</span>}
      {running && <span style={{ color: 'var(--status-running)' }}>Simulating (tick {tick})</span>}

      {breadcrumb && <>
        <Sep />
        <span style={{ color: 'var(--text-1)', fontFamily: 'var(--font-mono)', maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {breadcrumb}
        </span>
      </>}

      <div style={{ flex: 1 }} />
      <span style={{ fontFamily: 'var(--font-mono)' }}>{Math.round(zoom * 100)}%</span>
    </div>
  );
}

function Sep() {
  return <div style={{ width: 1, height: 12, background: 'var(--border-0)' }} />;
}
