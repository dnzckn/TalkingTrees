import { useSimStore } from '../store/simulationStore';

export function Timeline() {
  const { running, tick, tps, history, play, pause, step, reset, setTps, blackboard } = useSimStore();

  const statusColor = (s: string) =>
    s === 'SUCCESS' ? 'var(--success)' :
    s === 'FAILURE' ? 'var(--failure)' :
    s === 'RUNNING' ? 'var(--running)' : 'var(--t3)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      height: 'var(--timeline-h)', padding: '0 10px',
      background: 'var(--s1)', fontSize: 'var(--fs-sm)',
    }}>
      {/* Controls */}
      <button onClick={running ? pause : play} style={{
        width: 30, justifyContent: 'center',
        background: running ? 'var(--running)' : 'var(--success)',
        color: '#000', fontWeight: 700,
      }}>
        {running ? '⏸' : '▶'}
      </button>
      <button onClick={step} style={{ width: 30, justifyContent: 'center' }} title="Step (S)">⏭</button>
      <button onClick={reset} style={{ width: 30, justifyContent: 'center' }} title="Reset (R)">⏹</button>

      {/* Separator */}
      <div style={{ width: 1, height: 16, background: 'var(--b0)' }} />

      {/* TPS control */}
      <span style={{ color: 'var(--t2)', fontSize: 'var(--fs-xs)', fontWeight: 600 }}>TPS</span>
      <input
        type="range" min={0.5} max={50} step={0.5} value={tps}
        onChange={e => setTps(parseFloat(e.target.value))}
        style={{ width: 80, accentColor: 'var(--accent)' }}
      />
      <input
        type="number" min={0.1} max={100} step={0.1} value={tps}
        onChange={e => setTps(parseFloat(e.target.value) || 1)}
        style={{ width: 44, textAlign: 'center', fontFamily: 'var(--mono)', fontSize: 'var(--fs-xs)' }}
      />

      <div style={{ width: 1, height: 16, background: 'var(--b0)' }} />

      {/* Timeline track */}
      <div style={{
        flex: 1, height: 20, background: 'var(--s0)', borderRadius: 'var(--r-sm)',
        display: 'flex', alignItems: 'end', overflow: 'hidden', border: '1px solid var(--b0)',
      }}>
        {history.length === 0 ? (
          <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--t3)', fontSize: 'var(--fs-xs)' }}>
            Press ▶ or ⏭ to simulate
          </div>
        ) : (
          history.map((h, i) => (
            <div key={i} style={{
              flex: 1, minWidth: 2, height: '100%',
              background: statusColor(h.rootStatus),
              opacity: 0.7,
            }} />
          ))
        )}
      </div>

      {/* Tick counter */}
      <span style={{ fontFamily: 'var(--mono)', fontSize: 'var(--fs-xs)', color: 'var(--t1)', minWidth: 50, textAlign: 'right' }}>
        tick {tick}
      </span>

      {/* BB count */}
      <span style={{ fontFamily: 'var(--mono)', fontSize: 'var(--fs-xs)', color: 'var(--t2)' }}>
        BB:{blackboard.size}
      </span>
    </div>
  );
}
