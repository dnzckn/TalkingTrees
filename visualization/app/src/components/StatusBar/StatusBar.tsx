import { useTreeStore } from '../../store/treeStore';
import { useUIStore } from '../../store/uiStore';

export function StatusBar() {
  const { nodes, selectedIds, treeName, isDirty } = useTreeStore();
  const { zoom } = useUIStore();

  const nodeCount = Object.keys(nodes).length;
  const connCount = Object.values(nodes).reduce((s, n) => s + n.childIds.length, 0);
  const selCount = selectedIds.size;

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 14,
      height: 'var(--statusbar-h)', padding: '0 12px',
      background: '#0066b8', color: 'rgba(255,255,255,0.9)',
      fontSize: 'var(--fs-xs)', fontFamily: 'var(--font)',
    }}>
      <Item>{isDirty ? '●' : '◦'} {treeName}</Item>
      <Item>Nodes: {nodeCount}</Item>
      <Item>Connections: {connCount}</Item>
      {selCount > 0 && <Item>Selected: {selCount}</Item>}
      <div style={{ flex: 1 }} />
      <Item>Right-click for context menu</Item>
      <Item>Drag bottom port ● to connect</Item>
      <Item style={{ fontFamily: 'var(--font-mono)' }}>{Math.round(zoom * 100)}%</Item>
    </div>
  );
}

function Item({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <span style={style}>{children}</span>;
}
