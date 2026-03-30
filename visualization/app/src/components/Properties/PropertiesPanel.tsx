import { useTreeStore } from '../../store/treeStore';
import { getNodeTypeInfo } from '../Palette/nodeRegistry';

export function PropertiesPanel() {
  const { nodes, selectedIds, updateNode, deleteNode } = useTreeStore();

  const selectedId = [...selectedIds][0];
  const node = selectedId ? nodes[selectedId] : null;

  if (!node) {
    return (
      <div style={{ padding: 16, color: 'var(--text-secondary)' }}>
        <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 'var(--font-size-md)' }}>Properties</div>
        <p style={{ fontSize: 'var(--font-size-sm)' }}>Select a node to edit its properties.</p>
      </div>
    );
  }

  const info = getNodeTypeInfo(node.nodeType);

  const handleNameChange = (name: string) => updateNode(node.id, { name });

  const handleConfigChange = (key: string, value: unknown) => {
    updateNode(node.id, { config: { ...node.config, [key]: value } });
  };

  return (
    <div style={{ padding: 12, fontSize: 'var(--font-size-sm)' }}>
      <div style={{ fontWeight: 600, marginBottom: 12, fontSize: 'var(--font-size-md)' }}>Properties</div>

      {/* Node name */}
      <Field label="Name">
        <input value={node.name} onChange={(e) => handleNameChange(e.target.value)} style={{ width: '100%' }} />
      </Field>

      {/* Node type (read-only) */}
      <Field label="Type">
        <span style={{ color: info?.color || 'var(--text-primary)', fontWeight: 500 }}>
          {node.nodeType}
        </span>
      </Field>

      {/* Description */}
      <Field label="Description">
        <textarea
          value={node.description || ''}
          onChange={(e) => updateNode(node.id, { description: e.target.value || undefined })}
          rows={2}
          style={{ width: '100%', resize: 'vertical' }}
        />
      </Field>

      {/* Config fields */}
      <div style={{ borderTop: '1px solid var(--border)', marginTop: 12, paddingTop: 12 }}>
        <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>Configuration</div>
        {Object.entries(node.config).map(([key, value]) => (
          <Field key={key} label={key}>
            {typeof value === 'boolean' ? (
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => handleConfigChange(key, e.target.checked)}
              />
            ) : typeof value === 'number' ? (
              <input
                type="number"
                value={value}
                onChange={(e) => handleConfigChange(key, parseFloat(e.target.value) || 0)}
                style={{ width: '100%' }}
              />
            ) : (
              <input
                type="text"
                value={String(value ?? '')}
                onChange={(e) => handleConfigChange(key, e.target.value)}
                style={{ width: '100%' }}
              />
            )}
          </Field>
        ))}
      </div>

      {/* Blackboard contracts */}
      {(node.blackboardInput || node.blackboardOutput) && (
        <div style={{ borderTop: '1px solid var(--border)', marginTop: 12, paddingTop: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>Blackboard Contracts</div>
          {node.blackboardInput && (
            <div>
              <span style={{ color: '#4fc1ff', fontSize: '10px' }}>● INPUTS</span>
              {Object.entries(node.blackboardInput).map(([key, port]) => (
                <div key={key} style={{ paddingLeft: 12, fontSize: '11px', marginTop: 2 }}>
                  <span style={{ fontWeight: 500 }}>{key}</span>: {port.type}
                  {port.required && <span style={{ color: '#f44336' }}> *</span>}
                </div>
              ))}
            </div>
          )}
          {node.blackboardOutput && (
            <div style={{ marginTop: 6 }}>
              <span style={{ color: '#4caf50', fontSize: '10px' }}>● OUTPUTS</span>
              {Object.entries(node.blackboardOutput).map(([key, port]) => (
                <div key={key} style={{ paddingLeft: 12, fontSize: '11px', marginTop: 2 }}>
                  <span style={{ fontWeight: 500 }}>{key}</span>: {port.type}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Macro metadata */}
      {node.macro && (
        <div style={{ borderTop: '1px solid var(--border)', marginTop: 12, paddingTop: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--text-secondary)' }}>Macro</div>
          <Field label="Macro Name">
            <input value={node.macro.name} onChange={(e) => updateNode(node.id, { macro: { ...node.macro!, name: e.target.value } })} style={{ width: '100%' }} />
          </Field>
          <Field label="Color">
            <input type="color" value={node.macro.color || '#4ec9b0'} onChange={(e) => updateNode(node.id, { macro: { ...node.macro!, color: e.target.value } })} />
          </Field>
        </div>
      )}

      {/* Delete button */}
      <div style={{ marginTop: 16 }}>
        <button
          onClick={() => deleteNode(node.id)}
          style={{ background: '#c62828', color: 'white', width: '100%', padding: '6px 0' }}
        >
          Delete Node
        </button>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 8 }}>
      <label style={{ display: 'block', color: 'var(--text-secondary)', marginBottom: 2, fontSize: '11px' }}>
        {label}
      </label>
      {children}
    </div>
  );
}
