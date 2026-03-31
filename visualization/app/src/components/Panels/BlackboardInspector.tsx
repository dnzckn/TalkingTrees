import { useSimStore } from '../../store/simulationStore';

export function BlackboardInspector({ onClose }: { onClose: () => void }) {
  const { blackboard, tick } = useSimStore();

  const entries = Array.from(blackboard.entries());

  return (
    <div style={{
      position: 'absolute', top: 50, right: 10, width: 280, maxHeight: 400,
      background: 'var(--s2)', border: '1px solid var(--b1)',
      borderRadius: 'var(--r-md)', boxShadow: '0 8px 32px rgba(0,0,0,0.5)',
      zIndex: 100, display: 'flex', flexDirection: 'column', overflow: 'hidden',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 12px', borderBottom: '1px solid var(--b0)',
        fontWeight: 600, fontSize: 'var(--fs-sm)',
      }}>
        <span>Blackboard (tick {tick})</span>
        <button onClick={onClose} style={{ background: 'transparent', padding: '2px 6px', fontSize: 'var(--fs-sm)' }}>✕</button>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: 4 }}>
        {entries.length === 0 ? (
          <div style={{ padding: 12, color: 'var(--t3)', fontSize: 'var(--fs-sm)', textAlign: 'center' }}>
            No variables set. Run simulation to populate.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--fs-sm)' }}>
            <thead>
              <tr style={{ color: 'var(--t2)', fontSize: 'var(--fs-xs)', textAlign: 'left' }}>
                <th style={{ padding: '4px 8px', borderBottom: '1px solid var(--b0)' }}>Key</th>
                <th style={{ padding: '4px 8px', borderBottom: '1px solid var(--b0)' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(([key, val]) => (
                <tr key={key} style={{ borderBottom: '1px solid var(--b0)' }}>
                  <td style={{ padding: '4px 8px', fontFamily: 'var(--mono)', color: 'var(--accent)' }}>{key}</td>
                  <td style={{ padding: '4px 8px', fontFamily: 'var(--mono)', color: 'var(--t1)' }}>
                    {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
