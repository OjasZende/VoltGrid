import { useState, useEffect } from "react";
import { Battery, Activity, ShieldCheck, Zap } from "lucide-react";

export default function V2CMonitor() {
  const [qTable, setQTable] = useState([
    [1.24, 0.87, -0.43],
    [0.95, 1.12, 0.12],
    [-0.22, 0.65, 1.44]
  ]);
  const [activeCell, setActiveCell] = useState([1, 1]);
  const [history, setHistory] = useState([10, 25, 18, 45, 62, 58, 89, 112, 124]);

  useEffect(() => {
    const id = setInterval(() => {
      // Randomly update Q-table values slightly
      setQTable(prev => prev.map(row => row.map(val => +(val + (Math.random() * 0.1 - 0.05)).toFixed(2))));
      // Randomly change active cell
      setActiveCell([Math.floor(Math.random() * 3), Math.floor(Math.random() * 3)]);
      // Update history
      setHistory(prev => [...prev.slice(1), prev[prev.length - 1] + Math.round(Math.random() * 20 - 5)]);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="v2c-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 className="page-title">V2C Monitor</h1>
          <p className="page-subtitle">REINFORCEMENT LEARNING AGENT & GRID STRESS CONTROL</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <div className="live-badge" style={{ background: 'rgba(139, 92, 246, 0.05)', color: '#8b5cf6', textTransform: 'uppercase' }}>EPISODE 42</div>
          <div className="live-badge" style={{ background: 'rgba(16, 185, 129, 0.05)', color: '#10b981', textTransform: 'uppercase' }}>SYSTEM LIVE</div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="stat-card">
          <div className="stat-label">GRID STRESS</div>
          <div className="stat-value" style={{ color: 'var(--warning)' }}>MEDIUM</div>
          <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)' }}>PHASE 2 MONITORING</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">LAST ACTION</div>
          <div className="stat-value" style={{ color: 'var(--accent)' }}>ACTIVATE V2C</div>
          <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)' }}>REWARD: +10</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">CUMULATIVE REWARD</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>+124</div>
          <div className="stat-delta up">↑ 8.2% vs EP 41</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">AGENT STATUS</div>
          <div className="stat-value" style={{ fontSize: '1.2rem', marginTop: '8px' }}>STABLE</div>
          <div style={{ fontSize: '0.7rem', fontWeight: '700', color: 'var(--text-muted)' }}>EPSILON: 0.12</div>
        </div>
      </div>

      <div className="chart-container">
        <div className="chart-card">
          <h3 className="chart-title" style={{ marginBottom: '24px' }}>AGENT LEARNING CURVE</h3>
          <div style={{ height: '250px', position: 'relative' }}>
            <svg width="100%" height="100%" viewBox="0 0 800 250" preserveAspectRatio="none">
               <path 
                 d={history.map((v, i) => `${i === 0 ? 'M' : 'L'} ${(i / (history.length - 1)) * 800} ${250 - (v / 150) * 250}`).join(" ")} 
                 fill="none" stroke="var(--accent)" strokeWidth="3" 
               />
               <circle cx={800} cy={250 - (history[history.length-1] / 150) * 250} r="5" fill="var(--accent)" />
            </svg>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
              <span>EPISODE 0</span>
              <span>EPISODE 42</span>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title" style={{ marginBottom: '24px' }}>Q-TABLE (STATE-ACTION VALUES)</h3>
          <div style={{ overflow: 'hidden', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: '12px', textAlign: 'left', color: 'var(--text-muted)' }}>STATE\ACT</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>ACTIVATE</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>HOLD</th>
                  <th style={{ padding: '12px', textAlign: 'center', color: 'var(--text-muted)' }}>DEACTIVATE</th>
                </tr>
              </thead>
              <tbody>
                {["LOW", "MED", "HIGH"].map((state, r) => (
                  <tr key={state} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '12px', fontWeight: '700', color: 'var(--text-muted)' }}>{state}</td>
                    {qTable[r].map((val, c) => (
                      <td 
                        key={c} 
                        style={{ 
                          padding: '12px', 
                          textAlign: 'center', 
                          fontWeight: '700',
                          color: activeCell[0] === r && activeCell[1] === c ? 'var(--accent)' : '#fff',
                          background: activeCell[0] === r && activeCell[1] === c ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
                          transition: 'all 0.3s'
                        }}
                      >
                        {val > 0 ? `+${val.toFixed(2)}` : val.toFixed(2)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="chart-card" style={{ marginTop: '24px' }}>
        <h3 className="chart-title" style={{ marginBottom: '20px' }}>DECISION LOG</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { time: "18:42:01", state: "MED", action: "ACTIVATE V2C", reward: "+10" },
            { time: "18:41:56", state: "HIGH", action: "ACTIVATE V2C", reward: "+10" },
            { time: "18:41:51", state: "LOW", action: "HOLD", reward: "+2" },
            { time: "18:41:46", state: "LOW", action: "DEACTIVATE", reward: "-5" },
          ].map((log, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', padding: '12px 20px', background: 'rgba(15,23,42,0.3)', borderRadius: '8px', borderLeft: `3px solid ${i === 0 ? 'var(--accent)' : 'var(--border-color)'}` }}>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', width: '80px' }}>{log.time}</span>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--warning)', width: '60px' }}>{log.state}</span>
              <span style={{ margin: '0 16px', color: 'var(--text-muted)' }}>→</span>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--accent)', flex: 1 }}>{log.action}</span>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: log.reward.startsWith('+') ? 'var(--success)' : 'var(--danger)' }}>{log.reward}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
