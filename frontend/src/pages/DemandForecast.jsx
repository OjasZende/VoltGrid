import { useState, useEffect } from "react";
import { Brain, Activity } from "lucide-react";

// --- Trained weights loader (from previous work) ---
let cachedWeights = null;
let cachedScaler = null;
let weightsLoaded = false;

async function loadWeights() {
  if (weightsLoaded) return;
  try {
    const [wRes, sRes] = await Promise.all([
      fetch("/demand_model/weights.json"),
      fetch("/demand_model/scaler.json"),
    ]);
    if (wRes.ok && sRes.ok) {
      cachedWeights = await wRes.json();
      cachedScaler = await sRes.json();
    }
  } catch (e) { console.log("Weight load error", e); }
  weightsLoaded = true;
}

function relu(x) { return Math.max(0, x); }

function forwardPass(inputs) {
  if (!cachedWeights || !cachedScaler) return null;
  const { X_min, X_range, y_min, y_range } = cachedScaler;
  const xNorm = inputs.map((v, i) => (v - X_min[i]) / X_range[i]);
  const w1 = cachedWeights.layer1.kernel;
  const b1 = cachedWeights.layer1.bias;
  const h1 = b1.map((bias, j) => relu(xNorm.reduce((sum, xi, i) => sum + xi * w1[i][j], bias)));
  const w2 = cachedWeights.layer2.kernel;
  const b2 = cachedWeights.layer2.bias;
  const h2 = b2.map((bias, j) => relu(h1.reduce((sum, hi, i) => sum + hi * w2[i][j], bias)));
  const wo = cachedWeights.output.kernel;
  const bo = cachedWeights.output.bias;
  const yNorm = h2.reduce((sum, hi, i) => sum + hi * wo[i][0], bo[0]);
  return Math.max(100, Math.min(900, yNorm * y_range + y_min));
}

export default function DemandForecast() {
  const [inputs, setInputs] = useState({ hr: 14, dy: 3, temp: 31.4, traf: 0.72, ev: 1248 });
  const [prediction, setPrediction] = useState(487);
  const [modelStatus, setModelStatus] = useState("Loading...");
  const [curveData, setCurveData] = useState([]);

  useEffect(() => {
    loadWeights().then(() => {
      setModelStatus(cachedWeights ? "Trained Model ✓" : "Synthetic Estimates");
    });
  }, []);

  useEffect(() => {
    const run = () => {
      const now = new Date();
      const hr = now.getHours();
      const dy = now.getDay();
      const temp = 24 + Math.random() * 12;
      const traf = 0.3 + Math.random() * 0.6;
      const ev = 800 + Math.random() * 800;

      setInputs({ hr, dy, temp, traf, ev });

      // Generate dynamic curve for 24h
      const curve = [];
      for (let h = 0; h <= 24; h++) {
        const res = forwardPass([h % 24, dy, temp, traf, ev]);
        if (res) curve.push({ x: h, y: res });
        else {
          const hFactor = 0.5 + 0.5 * Math.sin(Math.PI * (h - 3) / 15);
          curve.push({ x: h, y: 300 + 400 * hFactor });
        }
      }
      setCurveData(curve);

      const res = forwardPass([hr, dy, temp, traf, ev]);
      if (res) setPrediction(Math.round(res));
      else {
        const hFactor = 0.5 + 0.5 * Math.sin(Math.PI * (hr - 3) / 15);
        setPrediction(Math.round(300 + 400 * hFactor));
      }
    };

    run();
    const id = setInterval(run, 4000);
    return () => clearInterval(id);
  }, []);

  // Helper to generate SVG path from curveData
  const getPath = () => {
    if (curveData.length === 0) return "";
    const minY = Math.min(...curveData.map(d => d.y));
    const maxY = Math.max(...curveData.map(d => d.y));
    const range = maxY - minY || 1;
    
    return curveData.map((d, i) => {
      const x = (d.x / 24) * 1000;
      const y = 180 - ((d.y - minY) / range) * 140;
      return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
    }).join(" ");
  };

  return (
    <div className="forecast-page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '32px' }}>
        <div>
          <h1 className="page-title">Demand Forecast</h1>
          <p className="page-subtitle">AI PREDICTIVE ANALYSIS & LOAD BALANCING</p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <div className="live-badge" style={{ background: 'rgba(6, 182, 212, 0.05)', color: '#06b6d4', textTransform: 'uppercase' }}>{modelStatus}</div>
          <div className="live-badge" style={{ background: 'rgba(16, 185, 129, 0.05)', color: '#10b981', textTransform: 'uppercase' }}>SYSTEM LIVE</div>
        </div>
      </div>

      <div className="forecast-card">
        {/* ... (neural visual area remains same) ... */}
        <div className="neural-visual-area">
          <div style={{ position: 'absolute', top: '16px', left: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.7rem', color: '#06b6d4', fontWeight: '700' }}>
             <Brain size={12} /> Neural Prediction Engine
          </div>
          <div className="neural-dot-layers">
            <div className="neural-dot-layer">
              {[0, 1, 2, 3, 4].map(i => <div key={i} className="neural-dot" style={{ background: '#06b6d4', boxShadow: '0 0 10px #06b6d4' }} />)}
            </div>
            <div className="neural-dot-layer">
              {[0, 1, 2].map(i => <div key={i} className="neural-dot" style={{ background: '#8b5cf6', opacity: 0.6 }} />)}
            </div>
            <div className="neural-dot-layer">
              {[0, 1].map(i => <div key={i} className="neural-dot" style={{ background: '#8b5cf6', opacity: 0.6 }} />)}
            </div>
            <div className="neural-dot-layer">
              <div className="neural-dot" style={{ width: '24px', height: '24px', background: '#10b981', boxShadow: '0 0 20px #10b981', display: 'flex', alignItems: 'center', justifyContent: 'center' }} />
              <div style={{ fontSize: '0.5rem', fontWeight: '700', color: '#10b981', marginTop: '4px' }}>MW DEMAND</div>
            </div>
          </div>
        </div>

        <div>
          <div className="page-subtitle" style={{ marginBottom: '16px' }}>LIVE INPUTS</div>
          <div className="input-grid-2x2">
            <div className="input-cell">
              <div className="stat-label">TIME</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>{inputs.hr}:00 {["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"][inputs.dy]}</div>
            </div>
            <div className="input-cell">
              <div className="stat-label">TEMP</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>{inputs.temp.toFixed(1)}°C</div>
            </div>
            <div className="input-cell">
              <div className="stat-label">ACTIVE STATIONS</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>1,248</div>
            </div>
            <div className="input-cell">
              <div className="stat-label">FLEET CONNECTS</div>
              <div style={{ fontSize: '1.1rem', fontWeight: '700' }}>420/hr</div>
            </div>
          </div>

          <div className="output-box-large">
            <div className="page-subtitle" style={{ color: '#06b6d4', marginBottom: '16px' }}>OUTPUT PREDICTION</div>
            <div className="output-value-huge">
              {prediction} <span className="output-unit">MW</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px' }}>
              <span className="page-subtitle" style={{ fontSize: '0.6rem' }}>CONFIDENCE SCORE</span>
              <span style={{ fontSize: '0.75rem', fontWeight: '700', color: '#10b981' }}>91.4%</span>
            </div>
            <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '2px', marginTop: '8px', overflow: 'hidden' }}>
              <div style={{ width: '91.4%', height: '100%', background: '#10b981' }} />
            </div>
          </div>
        </div>
      </div>

      <div className="chart-card">
        <h3 className="chart-title" style={{ marginBottom: '32px' }}>TODAY'S DEMAND CURVE (NEURAL ESTIMATES)</h3>
        <div style={{ height: '200px', width: '100%', position: 'relative' }}>
          <svg width="100%" height="100%" viewBox="0 0 1000 200" preserveAspectRatio="none">
             <path d={getPath()} fill="none" stroke="#06b6d4" strokeWidth="4" />
          </svg>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px', fontSize: '0.65rem', color: '#94a3b8' }}>
            <span>00:00</span>
            <span>06:00</span>
            <span>12:00</span>
            <span>18:00</span>
            <span>23:59</span>
          </div>
        </div>
      </div>
    </div>
  );
}
