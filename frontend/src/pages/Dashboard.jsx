import { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Polygon, CircleMarker, Marker, Circle } from 'react-leaflet';
import { Zap, AlertTriangle } from 'lucide-react';
import L from 'leaflet';

// Fix for default marker icon in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom bolt icon for selected stations
const boltIcon = new L.DivIcon({
  html: `<div style="background-color: #22c55e; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 10px rgba(34, 197, 94, 0.5); border: 2px solid white;">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
         </div>`,
  className: 'custom-bolt-icon',
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const API_BASE_URL = 'http://localhost:8000';
const CENTER = [19.0760, 72.8777]; // Mumbai
const ZOOM = 13;
const BASEMAP = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png";

export default function Dashboard() {
  const [data, setData] = useState({
    candidateSites: [],
    demandPoints: [],
    demandWeights: {},
    hexPolys: [],
    maxWeight: 1
  });
  const [optimization, setOptimization] = useState({
    selectedSites: [],
    coveredWeight: 0,
    totalWeight: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Controls
  const [k, setK] = useState(10);
  const [showHexagons, setShowHexagons] = useState(true);
  const [showWeights, setShowWeights] = useState(true);
  const [activeTab, setActiveTab] = useState('after'); // 'before' or 'after'

  // Load initial spatial data
  useEffect(() => {
    fetch(`${API_BASE_URL}/api/spatial-data`)
      .then(res => {
        if (!res.ok) throw new Error(`Server returned ${res.status}`);
        return res.json();
      })
      .then(json => {
        if (!json.candidateSites) throw new Error("Invalid data format received from API");
        setData(json);
        setLoading(false);
        setError(null);
      })
      .catch(err => {
        console.error("Error loading spatial data:", err);
        setError("Failed to load map data from backend. Make sure the Python server is running without errors.");
        setLoading(false);
      });
  }, []);

  // Run optimization when K changes or after initial load
  useEffect(() => {
    if (!data.candidateSites || data.candidateSites.length === 0) return;
    
    setLoading(true);
    fetch(`${API_BASE_URL}/api/optimize?k=${k}`)
      .then(res => {
        if (!res.ok) throw new Error(`Optimization failed with status ${res.status}`);
        return res.json();
      })
      .then(json => {
        if (!json.selectedSites) throw new Error("Invalid optimization format from API");
        setOptimization(json);
        setLoading(false);
        setError(null);
      })
      .catch(err => {
        console.error("Error optimizing:", err);
        setError("Failed to run optimization algorithm. Please check backend logs.");
        setLoading(false);
      });
  }, [k, data.candidateSites]);

  const weightToColor = (weight, maxWeight) => {
    if (!maxWeight || maxWeight === 0 || !weight || weight === 0) return { color: "#334155", opacity: 0.1 };
    const ratio = Math.min(weight / maxWeight, 1.0);
    // Interpolate from light yellow -> deep orange/red
    const r = 255;
    const g = Math.floor(200 - ratio * 160);
    const b = Math.floor(50 - ratio * 50);
    return { 
      color: `rgb(${r}, ${g}, ${b})`, 
      opacity: 0.15 + ratio * 0.5 
    };
  };

  const selectedSet = useMemo(() => {
    const sites = optimization.selectedSites || [];
    return new Set(sites.map(s => `${s[0]},${s[1]}`));
  }, [optimization.selectedSites]);

  return (
    <div className="dashboard-container">
      {loading && !error && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Processing Spatial Data...</p>
        </div>
      )}

      {error && (
        <div className="loading-overlay" style={{ background: "rgba(15, 23, 42, 0.95)" }}>
          <AlertTriangle size={48} color="#ef4444" style={{ marginBottom: "16px" }} />
          <h2 style={{ color: "#ef4444", marginBottom: "8px" }}>Connection Error</h2>
          <p style={{ maxWidth: "400px", textAlign: "center", color: "#f8fafc" }}>{error}</p>
        </div>
      )}

      {/* Sidebar Controls */}
      <div className="sidebar">
        <div className="sidebar-header">
          <h1 className="sidebar-title"><Zap size={24} /> VoltGrid</h1>
          <p className="sidebar-subtitle">Mumbai EV Station Optimizer</p>
        </div>

        <div className="control-group">
          <label className="control-label">Station Budget (K)</label>
          <div className="slider-container">
            <input 
              type="range" 
              min="1" 
              max="30" 
              value={k} 
              onChange={(e) => setK(parseInt(e.target.value))}
              disabled={!!error || (data.candidateSites && data.candidateSites.length === 0)}
            />
            <span className="slider-value">{k}</span>
          </div>
        </div>

        <div className="control-group">
          <label className="control-label">Map Layers</label>
          <label className="toggle-container">
            <input 
              type="checkbox" 
              checked={showHexagons} 
              onChange={(e) => setShowHexagons(e.target.checked)} 
            />
            Show Demand Grid (H3 Hexagons)
          </label>
          <label className="toggle-container">
            <input 
              type="checkbox" 
              checked={showWeights} 
              onChange={(e) => setShowWeights(e.target.checked)} 
              disabled={!showHexagons}
            />
            Color hexagons by POI weight
          </label>
        </div>

        <div className="legend">
          <div className="legend-title">Legend</div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: "#ef4444" }}></div>
            <span>Existing Site (Unoptimised)</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: "#22c55e", border: "1px solid white" }}></div>
            <span>Selected MCLP Station</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: "#64748b" }}></div>
            <span>Unselected Candidate</span>
          </div>
        </div>

        <div className="metrics-container">
          <div className="metric-card">
            <div className="metric-value">{(data.demandPoints || []).length}</div>
            <div className="metric-label">H3 Demand Points</div>
          </div>
          <div className="metric-card">
            <div className="metric-value">{(data.candidateSites || []).length}</div>
            <div className="metric-label">Candidate Sites</div>
          </div>
          <div className="metric-card" style={{ gridColumn: "span 2" }}>
            <div className="metric-value success">
              {optimization.totalWeight ? `${((optimization.coveredWeight / optimization.totalWeight) * 100).toFixed(1)}%` : '0%'}
            </div>
            <div className="metric-label">POI Weight Covered ({optimization.coveredWeight || 0} / {optimization.totalWeight || 0})</div>
          </div>
        </div>
      </div>

      {/* Main Map Content */}
      <div className="main-content">
        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'before' ? 'active' : ''}`}
            onClick={() => setActiveTab('before')}
          >
            🔴 Before (All Sites)
          </button>
          <button 
            className={`tab ${activeTab === 'after' ? 'active' : ''}`}
            onClick={() => setActiveTab('after')}
          >
            🟢 After (Optimized)
          </button>
        </div>

        <div className="map-container">
          <MapContainer center={CENTER} zoom={ZOOM} zoomControl={false} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url={BASEMAP}
              attribution='&copy; <a href="https://carto.com/attributions">CARTO</a>'
            />
            
            {/* Hexagon Grid */}
            {showHexagons && (data.hexPolys || []).map((poly, idx) => {
              const weight = (data.demandWeights && data.demandWeights[idx]) ? data.demandWeights[idx] : 0;
              const { color, opacity } = showWeights ? weightToColor(weight, data.maxWeight) : { color: "#64748b", opacity: 0.15 };
              return (
                <Polygon 
                  key={`hex-${idx}`}
                  positions={poly}
                  pathOptions={{
                    color: "#475569",
                    weight: 0.5,
                    fillColor: color,
                    fillOpacity: opacity
                  }}
                />
              );
            })}

            {/* Before Tab: Show all existing sites in red */}
            {activeTab === 'before' && (data.candidateSites || []).map((site, idx) => (
              <CircleMarker 
                key={`site-before-${idx}`}
                center={site}
                radius={7}
                pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.8 }}
              />
            ))}

            {/* After Tab: Show optimized sites and dimmed unselected ones */}
            {activeTab === 'after' && (data.candidateSites || []).map((site, idx) => {
              const isSelected = selectedSet.has(`${site[0]},${site[1]}`);
              
              if (isSelected) {
                return (
                  <div key={`sel-${idx}`}>
                    <Marker position={site} icon={boltIcon} />
                    <Circle 
                      center={site}
                      radius={2000} // Assuming 2000m radius as in original
                      pathOptions={{ color: '#22c55e', weight: 1.5, fillColor: '#22c55e', fillOpacity: 0.08 }}
                    />
                  </div>
                );
              } else {
                return (
                  <CircleMarker 
                    key={`cand-${idx}`}
                    center={site}
                    radius={4}
                    pathOptions={{ color: '#64748b', fillColor: '#94a3b8', fillOpacity: 0.4 }}
                  />
                );
              }
            })}
          </MapContainer>
        </div>
      </div>
    </div>
  );
}
