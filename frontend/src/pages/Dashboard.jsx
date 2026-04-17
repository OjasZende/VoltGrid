import { useState, useEffect } from "react";
import { Zap, Car, Leaf, Share2 } from "lucide-react";

export default function Dashboard() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));
  const [points, setPoints] = useState([]);

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Generate realistic demand points for 24h
    const newPoints = [];
    for (let h = 0; h <= 24; h += 2) {
      const hFactor = 0.5 + 0.5 * Math.sin(Math.PI * (h - 6) / 12);
      const val = 150 + 400 * hFactor + (Math.random() * 50);
      newPoints.push({ h: `${h.toString().padStart(2, '0')}:00`, v: val });
    }
    setPoints(newPoints);
  }, []);

  const maxV = 700;
  const svgW = 800;
  const svgH = 300;

  const getX = (i) => (i / (points.length - 1)) * svgW;
  const getY = (v) => svgH - (v / maxV) * svgH;

  const pathData = points.length > 0 ? points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getY(p.v)}`).join(" ") : "";
  const areaData = points.length > 0 ? `${pathData} L ${svgW} ${svgH} L 0 ${svgH} Z` : "";

  // Current time position
  const now = new Date();
  const currentHourPercent = (now.getHours() * 60 + now.getMinutes()) / (24 * 60);
  const cursorX = currentHourPercent * svgW;

  return (
    <div className="dashboard-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '32px' }}>
        <div className="page-title-group">
          <h1 className="page-title">GRID OVERVIEW</h1>
          <p className="page-subtitle">MUMBAI REAL-TIME TELEMETRY</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--accent)', fontFamily: 'monospace' }}>{time} IST</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '700', marginTop: '4px' }}>LAST SYNC: JUST NOW</div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="stat-card">
          <div className="stat-label">TOTAL STATIONS</div>
          <div className="stat-value">500</div>
          <div className="stat-delta up">↑ +12 this week</div>
          <Zap className="stat-icon-bg" />
        </div>
        <div className="stat-card">
          <div className="stat-label">EVS COVERED</div>
          <div className="stat-value">1,00,000</div>
          <div className="stat-delta up">↑ +4.2% MoM</div>
          <Car className="stat-icon-bg" />
        </div>
        <div className="stat-card">
          <div className="stat-label">GRID STRESS SAVED</div>
          <div className="stat-value">34%</div>
          <div className="stat-delta" style={{ color: 'var(--success)' }}>Optimal Level</div>
          <Leaf className="stat-icon-bg" />
        </div>
        <div className="stat-card">
          <div className="stat-label">ACTIVE V2C NODES</div>
          <div className="stat-value">1,240</div>
          <div className="stat-delta" style={{ color: 'var(--warning)' }}>⚠️ 8 nodes degraded</div>
          <Share2 className="stat-icon-bg" />
        </div>
      </div>

      <div className="chart-container">
        <div className="chart-card">
          <div className="chart-header" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <h3 className="chart-title">TODAY'S DEMAND CURVE</h3>
            <span style={{ fontSize: '0.6rem', background: '#1e293b', padding: '2px 6px', borderRadius: '4px', color: 'var(--text-muted)' }}>MW/H</span>
          </div>
          <div style={{ position: 'relative', height: `${svgH}px` }}>
            <svg width="100%" height="100%" viewBox={`0 0 ${svgW} ${svgH}`} preserveAspectRatio="none">
              <defs>
                <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.2" />
                  <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
                </linearGradient>
              </defs>
              {[0, 0.25, 0.5, 0.75, 1].map(p => (
                <line key={p} x1="0" y1={p * svgH} x2={svgW} y2={p * svgH} stroke="rgba(255,255,255,0.05)" strokeDasharray="4 4" />
              ))}
              {points.length > 0 && (
                <>
                  <path d={areaData} fill="url(#areaGrad)" />
                  <path d={pathData} fill="none" stroke="var(--accent)" strokeWidth="2" />
                  <line x1={cursorX} y1="0" x2={cursorX} y2={svgH} stroke="var(--accent)" strokeWidth="1" />
                  <circle cx={cursorX} cy={getY(points[Math.floor(currentHourPercent * (points.length / 2)) % points.length]?.v || 300)} r="4" fill="var(--success)" />
                </>
              )}
            </svg>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.65rem', color: 'var(--text-muted)' }}>
              <span>00:00</span>
              <span>06:00</span>
              <span>12:00</span>
              <span>18:00</span>
              <span>24:00</span>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h3 className="chart-title" style={{ marginBottom: '32px' }}>STATION STATUS MIX</h3>
          <div style={{ textAlign: 'center', marginBottom: '32px' }}>
            <div style={{ fontSize: '1.5rem', fontWeight: '700' }}>500</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Nodes</div>
          </div>
          <div className="status-mix-list">
            {[
              { label: "Available", val: "45%", color: "var(--success)" },
              { label: "Busy", val: "30%", color: "var(--warning)" },
              { label: "Overcrowded", val: "15%", color: "var(--danger)" },
              { label: "Offline", val: "10%", color: 'var(--text-muted)' },
            ].map(row => (
              <div key={row.label} className="status-row">
                <div className="status-label-group">
                  <span className="status-dot" style={{ background: row.color }} />
                  {row.label}
                </div>
                <span className="status-pct">{row.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
        <div className="live-badge" style={{ background: '#1e293b', border: '1px solid var(--border-color)', padding: '6px 16px' }}>SYSTEM: LIVE</div>
        <div className="live-badge" style={{ background: '#1e293b', border: '1px solid var(--border-color)', padding: '6px 16px', color: 'var(--accent)' }}>☁ UPTIME: 99.8%</div>
      </div>
    </div>
  );
}
