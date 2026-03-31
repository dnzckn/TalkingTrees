import { useState } from 'react';
import { useTreeStore } from '../../store/treeStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';

export function PropertiesPanel() {
  const { nodes, selectedIds, updateNode, deleteNode, setParent } = useTreeStore();
  const selectedId = [...selectedIds][0];
  const node = selectedId ? nodes[selectedId] : null;

  if (!node) {
    return (
      <div style={{ padding: 20, color: 'var(--t3)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8, marginTop: 40 }}>
        <span style={{ fontSize: 28, opacity: 0.3 }}>⚙</span>
        <span style={{ fontSize: 'var(--fs-sm)', textAlign: 'center' }}>Select a node to view<br />its properties</span>
      </div>
    );
  }

  const info = getNodeTypeInfo(node.nodeType);
  const accent = info?.color || 'var(--accent)';
  const parent = node.parentId ? nodes[node.parentId] : null;

  return (
    <div style={{ fontSize: 'var(--fs-sm)', animation: 'slideUp var(--dur-slow) var(--ease)' }}>
      {/* Node header */}
      <div style={{ padding: '12px 14px 10px', borderBottom: '1px solid var(--b0)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{
            width: 24, height: 24, borderRadius: 'var(--r-sm)',
            background: `${accent}20`, display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 13,
          }}>{info?.icon || '?'}</span>
          <div>
            <div style={{ fontWeight: 600, fontSize: 'var(--fs-lg)', lineHeight: 1.2 }}>{node.name}</div>
            <div style={{ fontSize: 'var(--fs-xs)', color: accent, fontWeight: 500 }}>{node.nodeType}</div>
          </div>
        </div>
        {info?.description && (
          <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--t2)', lineHeight: 1.4, marginTop: 4 }}>{info.description}</div>
        )}
      </div>

      {/* Name */}
      <Section title="Identity">
        <Field label="Name">
          <input value={node.name} onChange={e => updateNode(node.id, { name: e.target.value })} style={{ width: '100%' }} />
        </Field>
        <Field label="Description">
          <textarea value={node.description || ''} onChange={e => updateNode(node.id, { description: e.target.value || undefined })}
            rows={2} style={{ width: '100%', resize: 'vertical' }} placeholder="Optional description..." />
        </Field>
      </Section>

      {/* Config */}
      {Object.keys(node.config).length > 0 && (
        <Section title="Configuration">
          {Object.entries(node.config).filter(([k]) => !k.startsWith('_')).map(([key, value]) => (
            <Field key={key} label={key}>
              {typeof value === 'boolean' ? (
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={value} onChange={e => updateNode(node.id, { config: { ...node.config, [key]: e.target.checked } })}
                    style={{ accentColor: 'var(--accent)', width: 14, height: 14 }} />
                  <span style={{ color: value ? 'var(--success)' : 'var(--t2)' }}>{value ? 'true' : 'false'}</span>
                </label>
              ) : typeof value === 'number' ? (
                <input type="number" value={value} onChange={e => updateNode(node.id, { config: { ...node.config, [key]: parseFloat(e.target.value) || 0 } })} style={{ width: '100%' }} />
              ) : (
                <input type="text" value={String(value ?? '')} onChange={e => updateNode(node.id, { config: { ...node.config, [key]: e.target.value } })} style={{ width: '100%' }} />
              )}
            </Field>
          ))}
        </Section>
      )}

      {/* Connections */}
      <Section title="Connections">
        {parent ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0' }}>
            <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--t3)' }}>Parent:</span>
            <button onClick={() => useTreeStore.getState().selectNode(parent.id, false)} style={{ background: 'var(--s0)', fontSize: 'var(--fs-xs)' }}>
              {parent.name}
            </button>
            <button onClick={() => setParent(node.id, null)} style={{ background: 'none', color: 'var(--failure)', fontSize: 'var(--fs-xs)', padding: '2px 4px' }}>✕</button>
          </div>
        ) : (
          <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--t3)' }}>No parent (root node)</div>
        )}
        {node.childIds.length > 0 && (
          <div style={{ marginTop: 4 }}>
            <span style={{ fontSize: 'var(--fs-xs)', color: 'var(--t3)' }}>Children ({node.childIds.length}):</span>
            {node.childIds.map(cid => {
              const child = nodes[cid];
              return child ? (
                <button key={cid} onClick={() => useTreeStore.getState().selectNode(cid, false)}
                  style={{ display: 'block', background: 'var(--s0)', fontSize: 'var(--fs-xs)', marginTop: 3, width: '100%', textAlign: 'left' }}>
                  {child.name} <span style={{ color: 'var(--t3)' }}>({child.nodeType})</span>
                </button>
              ) : null;
            })}
          </div>
        )}
      </Section>

      {/* Blackboard */}
      {(node.blackboardInput || node.blackboardOutput) && (
        <Section title="Blackboard Contracts">
          {node.blackboardInput && Object.entries(node.blackboardInput).map(([k, p]) => (
            <div key={`in-${k}`} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 'var(--fs-xs)', padding: '2px 0' }}>
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>IN</span>
              <span style={{ fontFamily: 'var(--mono)', color: 'var(--t1)' }}>{k}</span>
              <span style={{ color: 'var(--t3)' }}>: {p.type}</span>
              {p.required && <span style={{ color: 'var(--failure)', fontSize: 8 }}>*</span>}
            </div>
          ))}
          {node.blackboardOutput && Object.entries(node.blackboardOutput).map(([k, p]) => (
            <div key={`out-${k}`} style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 'var(--fs-xs)', padding: '2px 0' }}>
              <span style={{ color: 'var(--success)', fontWeight: 600 }}>OUT</span>
              <span style={{ fontFamily: 'var(--mono)', color: 'var(--t1)' }}>{k}</span>
              <span style={{ color: 'var(--t3)' }}>: {p.type}</span>
            </div>
          ))}
        </Section>
      )}

      {/* Macro */}
      {node.macro && (
        <Section title="Macro">
          <Field label="Name">
            <input value={node.macro.name} onChange={e => updateNode(node.id, { macro: { ...node.macro!, name: e.target.value } })} style={{ width: '100%' }} />
          </Field>
          <Field label="Color">
            <input type="color" value={node.macro.color || accent} onChange={e => updateNode(node.id, { macro: { ...node.macro!, color: e.target.value } })} />
          </Field>
        </Section>
      )}

      {/* Delete */}
      <div style={{ padding: '12px 14px' }}>
        <button onClick={() => deleteNode(node.id)} style={{
          width: '100%', justifyContent: 'center', padding: '7px 0',
          background: 'rgba(240,104,104,0.1)', color: 'var(--failure)',
          border: '1px solid rgba(240,104,104,0.2)', fontWeight: 600,
        }}>
          Delete Node
        </button>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  const [open, setOpen] = useState(true);
  return (
    <div style={{ borderBottom: '1px solid var(--b0)' }}>
      <button onClick={() => setOpen(!open)} style={{
        width: '100%', justifyContent: 'flex-start', padding: '8px 14px',
        background: 'transparent', fontSize: 'var(--fs-xs)', fontWeight: 600,
        color: 'var(--t2)', textTransform: 'uppercase', letterSpacing: '0.5px',
      }}>
        <span style={{ fontSize: 7, marginRight: 4, display: 'inline-block', transition: 'transform var(--dur)', transform: open ? 'rotate(0)' : 'rotate(-90deg)' }}>▼</span>
        {title}
      </button>
      {open && <div style={{ padding: '0 14px 10px' }}>{children}</div>}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 7 }}>
      <label style={{ display: 'block', fontSize: 'var(--fs-xs)', color: 'var(--t3)', marginBottom: 3, fontWeight: 500 }}>{label}</label>
      {children}
    </div>
  );
}
