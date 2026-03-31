import { useState, useRef } from 'react';
import { getNodesBySection, type NodeTypeInfo } from './nodeRegistry';
import { useTreeStore } from '../../store/treeStore';

export function Palette() {
  const [search, setSearch] = useState('');
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({});
  const inputRef = useRef<HTMLInputElement>(null);
  const sections = getNodesBySection();

  const filtered = Object.entries(sections).reduce<Record<string, NodeTypeInfo[]>>(
    (acc, [section, items]) => {
      const f = search ? items.filter(n =>
        n.displayName.toLowerCase().includes(search.toLowerCase()) ||
        n.description.toLowerCase().includes(search.toLowerCase())
      ) : items;
      if (f.length > 0) acc[section] = f;
      return acc;
    }, {},
  );

  const onDragStart = (e: React.DragEvent, n: NodeTypeInfo) => {
    e.dataTransfer.setData('application/json', JSON.stringify(n));
    e.dataTransfer.effectAllowed = 'copy';
    // Create drag ghost
    const ghost = document.createElement('div');
    ghost.style.cssText = `padding:6px 12px; background:${n.color}22; border:1px solid ${n.color}; border-radius:6px; color:#fff; font:500 12px Inter,sans-serif; position:absolute; top:-100px;`;
    ghost.textContent = n.displayName;
    document.body.appendChild(ghost);
    e.dataTransfer.setDragImage(ghost, 40, 16);
    setTimeout(() => document.body.removeChild(ghost), 0);
  };

  const onDblClick = (n: NodeTypeInfo) => {
    useTreeStore.getState().addNode({
      nodeType: n.type, name: n.displayName, config: { ...n.defaultConfig },
      x: 300 + Math.random() * 100, y: 200 + Math.random() * 100,
    });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', userSelect: 'none' }}>
      {/* Header */}
      <div style={{ padding: '11px 14px 0', display: 'flex', alignItems: 'baseline', gap: 6 }}>
        <span style={{ fontWeight: 700, fontSize: 'var(--fs-lg)', letterSpacing: '-0.2px' }}>Nodes</span>
        <span style={{ fontSize: 'var(--fs-2xs)', color: 'var(--t3)', fontWeight: 500 }}>
          {Object.values(filtered).reduce((s, a) => s + a.length, 0)}
        </span>
      </div>

      {/* Search */}
      <div style={{ padding: '8px 12px' }}>
        <div style={{ position: 'relative' }}>
          <input ref={inputRef} type="text" placeholder="Search nodes..."
            value={search} onChange={e => setSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: 28, paddingRight: search ? 24 : 8, fontSize: 'var(--fs-sm)' }}
          />
          <span style={{ position: 'absolute', left: 9, top: '50%', transform: 'translateY(-50%)', color: 'var(--t3)', fontSize: 'var(--fs-sm)', pointerEvents: 'none' }}>⌕</span>
          {search && (
            <button onClick={() => setSearch('')} style={{ position: 'absolute', right: 4, top: '50%', transform: 'translateY(-50%)', background: 'none', padding: 2, color: 'var(--t3)', fontSize: 10 }}>✕</button>
          )}
        </div>
      </div>

      {/* Sections */}
      <div style={{ flex: 1, overflow: 'auto', padding: '0 6px 8px' }}>
        {Object.entries(filtered).map(([section, items]) => {
          const isCollapsed = collapsed[section];
          return (
            <div key={section} style={{ marginBottom: 2 }}>
              {/* Section header */}
              <button
                onClick={() => setCollapsed(c => ({ ...c, [section]: !c[section] }))}
                style={{
                  width: '100%', justifyContent: 'flex-start',
                  padding: '6px 8px', background: 'transparent',
                  fontSize: 'var(--fs-xs)', fontWeight: 600, color: 'var(--t2)',
                  textTransform: 'uppercase', letterSpacing: '0.6px',
                }}
              >
                <span style={{ width: 12, textAlign: 'center', fontSize: 8, transition: 'transform var(--dur) var(--ease)', transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0)', display: 'inline-block' }}>▼</span>
                <span style={{ flex: 1, textAlign: 'left' }}>{section}</span>
                <span style={{ fontWeight: 400, color: 'var(--t3)', fontFamily: 'var(--mono)', fontSize: 'var(--fs-2xs)' }}>{items.length}</span>
              </button>

              {/* Items */}
              {!isCollapsed && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 1, padding: '2px 0 4px' }}>
                  {items.map(n => (
                    <div
                      key={n.type}
                      draggable
                      onDragStart={e => onDragStart(e, n)}
                      onDoubleClick={() => onDblClick(n)}
                      title={n.description}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 8,
                        padding: '5px 8px 5px 10px',
                        marginLeft: 4, cursor: 'grab',
                        borderLeft: `2px solid ${n.color}30`,
                        borderRadius: '0 var(--r-sm) var(--r-sm) 0',
                        transition: 'all var(--dur) var(--ease)',
                        fontSize: 'var(--fs-sm)',
                      }}
                      onMouseEnter={e => {
                        e.currentTarget.style.background = `${n.color}0a`;
                        e.currentTarget.style.borderLeftColor = n.color;
                      }}
                      onMouseLeave={e => {
                        e.currentTarget.style.background = 'transparent';
                        e.currentTarget.style.borderLeftColor = `${n.color}30`;
                      }}
                    >
                      <span style={{
                        width: 22, height: 22, borderRadius: 'var(--r-sm)',
                        background: `${n.color}15`, display: 'flex',
                        alignItems: 'center', justifyContent: 'center',
                        fontSize: 12, flexShrink: 0,
                      }}>
                        {n.icon}
                      </span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontWeight: 500, color: 'var(--t0)', lineHeight: 1.3 }}>{n.displayName}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer hint */}
      <div style={{ padding: '7px 14px', borderTop: '1px solid var(--b0)', fontSize: 'var(--fs-2xs)', color: 'var(--t3)', display: 'flex', gap: 12 }}>
        <span>Drag to canvas</span>
        <span>Double-click to add</span>
      </div>
    </div>
  );
}
