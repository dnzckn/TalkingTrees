import { useEffect, useState } from 'react';
import { useTreeStore } from '../store/treeStore';

interface MenuPos { x: number; y: number; nodeId: string | null; worldX: number; worldY: number }

const QUICK_ADD = [
  { section: 'Composites', items: [
    { type: 'Sequence', icon: '→', name: 'Sequence' },
    { type: 'Selector', icon: '?', name: 'Selector' },
    { type: 'Parallel', icon: '⫴', name: 'Parallel' },
  ]},
  { section: 'Decorators', items: [
    { type: 'Inverter', icon: '¬', name: 'Inverter' },
    { type: 'Retry', icon: '↻', name: 'Retry' },
    { type: 'Timeout', icon: '⏱', name: 'Timeout' },
    { type: 'RateLimiter', icon: '⏩', name: 'Rate Limiter' },
    { type: 'Debounce', icon: '⏸', name: 'Debounce' },
  ]},
  { section: 'Actions', items: [
    { type: 'Success', icon: '✓', name: 'Success' },
    { type: 'Failure', icon: '✗', name: 'Failure' },
    { type: 'Running', icon: '~', name: 'Running' },
    { type: 'SetBlackboardVariable', icon: '✏', name: 'Set Variable' },
    { type: 'AsyncAction', icon: '⚡', name: 'Async Action' },
  ]},
  { section: 'Conditions', items: [
    { type: 'CheckBlackboardVariableValue', icon: '⚖', name: 'Check Value' },
    { type: 'CheckBlackboardVariableExists', icon: '?', name: 'Key Exists?' },
  ]},
  { section: 'References', items: [
    { type: 'SubTreeRef', icon: '🔗', name: 'Subtree Ref' },
    { type: 'RemoteSubtree', icon: '☁', name: 'Remote Subtree' },
  ]},
  { section: 'Resources', items: [
    { type: 'AcquireResource', icon: '🔒', name: 'Acquire Resource' },
    { type: 'ReleaseResource', icon: '🔓', name: 'Release Resource' },
  ]},
];

// Clipboard for copy/paste
let clipboard: { nodeType: string; name: string; config: Record<string, unknown> } | null = null;

export function ContextMenu() {
  const [menu, setMenu] = useState<MenuPos | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const { addNode, deleteNode, setParent, nodes, updateNode } = useTreeStore();

  useEffect(() => {
    const handler = (e: Event) => {
      setMenu((e as CustomEvent).detail);
      setShowAdd(false);
    };
    window.addEventListener('tree-context-menu', handler);
    return () => window.removeEventListener('tree-context-menu', handler);
  }, []);

  useEffect(() => {
    if (!menu) return;
    const close = (e: MouseEvent) => {
      if (!(e.target as HTMLElement).closest('.ctx-menu')) setMenu(null);
    };
    const esc = (e: KeyboardEvent) => { if (e.key === 'Escape') setMenu(null); };
    setTimeout(() => {
      window.addEventListener('mousedown', close);
      window.addEventListener('keydown', esc);
    }, 0);
    return () => {
      window.removeEventListener('mousedown', close);
      window.removeEventListener('keydown', esc);
    };
  }, [menu]);

  if (!menu) return null;

  const node = menu.nodeId ? nodes[menu.nodeId] : null;

  const doAdd = (type: string, name: string) => {
    const id = addNode({
      nodeType: type, name,
      x: menu.worldX + (node ? 0 : 0),
      y: menu.worldY + (node ? 80 : 0),
      config: {},
    });
    if (menu.nodeId) setParent(id, menu.nodeId);
    setMenu(null);
  };

  const doCopy = () => {
    if (node) clipboard = { nodeType: node.nodeType, name: node.name, config: { ...node.config } };
    setMenu(null);
  };

  const doPaste = () => {
    if (clipboard) {
      const id = addNode({ ...clipboard, x: menu.worldX, y: menu.worldY });
      if (menu.nodeId) setParent(id, menu.nodeId);
    }
    setMenu(null);
  };

  const doDuplicate = () => {
    if (node) {
      const id = addNode({ nodeType: node.nodeType, name: node.name + ' (copy)', config: { ...node.config }, x: node.x + 30, y: node.y + 30 });
      if (node.parentId) setParent(id, node.parentId);
    }
    setMenu(null);
  };

  const doDelete = () => { if (menu.nodeId) deleteNode(menu.nodeId); setMenu(null); };

  const doCollapse = () => {
    if (node) updateNode(node.id, { collapsed: !node.collapsed });
    setMenu(null);
  };

  const doSelectAll = () => {
    const store = useTreeStore.getState();
    for (const id of Object.keys(nodes)) store.selectNode(id, true);
    setMenu(null);
  };

  const doDisconnect = () => {
    if (node && node.parentId) setParent(node.id, null);
    setMenu(null);
  };

  return (
    <div className="ctx-menu" style={{
      position: 'fixed', left: menu.x, top: menu.y,
      background: 'var(--surface-2)', border: '1px solid var(--border-1)',
      borderRadius: 'var(--r-md)', padding: '4px 0', minWidth: 220,
      boxShadow: '0 8px 40px rgba(0,0,0,0.6)', zIndex: 9999,
      fontSize: 'var(--fs-sm)',
    }}>
      {/* ── Add Child / Add Node ── */}
      <div
        style={{ position: 'relative' }}
        onMouseEnter={() => setShowAdd(true)}
        onMouseLeave={() => setShowAdd(false)}
      >
        <Item icon="➕" label={node ? 'Add Child' : 'Add Node'} shortcut="▸" />
        {showAdd && (
          <div style={{
            position: 'absolute', left: '100%', top: -4,
            background: 'var(--surface-2)', border: '1px solid var(--border-1)',
            borderRadius: 'var(--r-md)', padding: '4px 0', minWidth: 200,
            boxShadow: '0 8px 40px rgba(0,0,0,0.6)', maxHeight: 450, overflow: 'auto',
          }}>
            {QUICK_ADD.map(s => (
              <div key={s.section}>
                <div style={{ padding: '4px 12px', fontSize: 'var(--fs-xs)', color: 'var(--text-2)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  {s.section}
                </div>
                {s.items.map(i => (
                  <Item key={i.type} icon={i.icon} label={i.name} onClick={() => doAdd(i.type, i.name)} />
                ))}
                <Sep />
              </div>
            ))}
          </div>
        )}
      </div>

      <Sep />

      {/* ── Node-specific actions ── */}
      {node && (<>
        <Item icon="📋" label="Copy" shortcut="Ctrl+C" onClick={doCopy} />
        <Item icon="✂️" label="Cut" shortcut="Ctrl+X" onClick={() => { doCopy(); doDelete(); }} />
      </>)}
      <Item icon="📄" label="Paste" shortcut="Ctrl+V" onClick={doPaste} disabled={!clipboard} />
      {node && (
        <Item icon="📑" label="Duplicate" shortcut="Ctrl+D" onClick={doDuplicate} />
      )}

      <Sep />

      {node && (<>
        <Item icon={node.collapsed ? '▸' : '▾'} label={node.collapsed ? 'Expand' : 'Collapse'} shortcut="C" onClick={doCollapse} />
        {node.parentId && (
          <Item icon="⊘" label="Disconnect" onClick={doDisconnect} />
        )}
      </>)}

      <Sep />

      {node && (
        <Item icon="🗑️" label="Delete" shortcut="Del" onClick={doDelete} danger />
      )}
      <Item icon="☑️" label="Select All" shortcut="Ctrl+A" onClick={doSelectAll} />
    </div>
  );
}

function Item({ icon, label, shortcut, onClick, disabled, danger }: {
  icon: string; label: string; shortcut?: string; onClick?: () => void; disabled?: boolean; danger?: boolean;
}) {
  return (
    <div
      onClick={disabled ? undefined : onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        padding: '6px 12px', cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.4 : 1,
        color: danger ? 'var(--status-failure)' : 'var(--text-0)',
        transition: 'background var(--duration)',
      }}
      onMouseEnter={e => { if (!disabled) e.currentTarget.style.background = 'var(--surface-hover)'; }}
      onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
    >
      <span style={{ width: 18, textAlign: 'center', fontSize: 'var(--fs-md)' }}>{icon}</span>
      <span style={{ flex: 1 }}>{label}</span>
      {shortcut && <span style={{ color: 'var(--text-3)', fontSize: 'var(--fs-xs)', fontFamily: 'var(--font-mono)' }}>{shortcut}</span>}
    </div>
  );
}

function Sep() {
  return <div style={{ height: 1, background: 'var(--border-0)', margin: '3px 10px' }} />;
}
