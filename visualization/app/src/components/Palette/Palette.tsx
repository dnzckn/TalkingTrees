import { useState } from 'react';
import { getNodesBySection, type NodeTypeInfo } from './nodeRegistry';
import { useTreeStore } from '../../store/treeStore';

export function Palette() {
  const [search, setSearch] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const sections = getNodesBySection();

  const filtered = Object.entries(sections).reduce<Record<string, NodeTypeInfo[]>>(
    (acc, [section, items]) => {
      const f = search
        ? items.filter(n => n.displayName.toLowerCase().includes(search.toLowerCase()) || n.type.toLowerCase().includes(search.toLowerCase()))
        : items;
      if (f.length > 0) acc[section] = f;
      return acc;
    }, {},
  );

  const onDragStart = (e: React.DragEvent, n: NodeTypeInfo) => {
    e.dataTransfer.setData('application/json', JSON.stringify(n));
    e.dataTransfer.effectAllowed = 'copy';
  };

  const onDblClick = (n: NodeTypeInfo) => {
    useTreeStore.getState().addNode({
      nodeType: n.type, name: n.displayName, config: { ...n.defaultConfig },
      x: 300 + Math.random() * 100, y: 200 + Math.random() * 100,
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{ padding: '10px 14px 6px', fontWeight: 700, fontSize: 'var(--fs-lg)', color: 'var(--text-1)' }}>
        Nodes
      </div>

      {/* Search */}
      <div style={{ padding: '0 10px 8px' }}>
        <input
          type="text" placeholder="Search..."
          value={search} onChange={e => setSearch(e.target.value)}
          style={{ width: '100%', padding: '5px 8px', fontSize: 'var(--fs-sm)' }}
        />
      </div>

      {/* Sections */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 4px 8px' }}>
        {Object.entries(filtered).map(([section, items]) => {
          const isCollapsed = collapsed[section];
          return (
            <div key={section} style={{ marginBottom: 2 }}>
              <div
                onClick={() => setCollapsed(c => ({ ...c, [section]: !c[section] }))}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '5px 10px', cursor: 'pointer', userSelect: 'none',
                  fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--text-2)',
                  textTransform: 'uppercase', letterSpacing: '0.8px',
                  borderRadius: 'var(--r-sm)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
              >
                <span style={{ fontSize: 8, transition: 'transform var(--duration)', transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0)' }}>▼</span>
                <span style={{ flex: 1 }}>{section}</span>
                <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--text-3)' }}>{items.length}</span>
              </div>

              {!isCollapsed && items.map(n => (
                <div
                  key={n.type}
                  draggable
                  onDragStart={e => onDragStart(e, n)}
                  onDoubleClick={() => onDblClick(n)}
                  title={n.description}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 8,
                    padding: '4px 8px 4px 22px', cursor: 'grab',
                    borderRadius: 'var(--r-sm)', fontSize: 'var(--fs-sm)',
                    transition: 'background var(--duration)',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface-hover)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <span style={{ width: 7, height: 7, borderRadius: '50%', background: n.color, flexShrink: 0, boxShadow: `0 0 4px ${n.color}40` }} />
                  <span style={{ flex: 1, color: 'var(--text-0)' }}>{n.displayName}</span>
                  <span style={{ fontSize: 9, color: 'var(--text-3)' }}>{n.icon}</span>
                </div>
              ))}
            </div>
          );
        })}
      </div>

      {/* Help hint */}
      <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border-0)', fontSize: 'var(--fs-xs)', color: 'var(--text-3)' }}>
        Drag to canvas or double-click to add
      </div>
    </div>
  );
}
