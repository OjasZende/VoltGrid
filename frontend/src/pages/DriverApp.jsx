import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { Navigation, Zap, AlertTriangle, CheckCircle, Loader, MapPin, Clock, Route } from "lucide-react";
import "leaflet/dist/leaflet.css";

// ── Proper SVG markers (no emojis) ──────────────────────────────────────────

const originIcon = new L.DivIcon({
  className: "",
  html: `<div style="
    width:22px;height:22px;
    background:#3b82f6;
    border:3px solid #fff;
    border-radius:50%;
    box-shadow:0 2px 8px rgba(0,0,0,0.5);
  "></div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

const destIcon = new L.DivIcon({
  className: "",
  html: `<svg width="24" height="34" viewBox="0 0 24 34" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 0C5.37 0 0 5.37 0 12c0 9 12 22 12 22s12-13 12-22C24 5.37 18.63 0 12 0z" fill="#ef4444" stroke="#fff" stroke-width="1.5"/>
    <circle cx="12" cy="12" r="5" fill="#fff"/>
  </svg>`,
  iconSize: [24, 34],
  iconAnchor: [12, 34],
});

const stationIcon = new L.DivIcon({
  className: "",
  html: `<div style="
    width:30px;height:30px;
    background:#16a34a;
    border:3px solid #fff;
    border-radius:50%;
    display:flex;align-items:center;justify-content:center;
    box-shadow:0 2px 8px rgba(0,0,0,0.5);
  ">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  </div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

// ──────────────────────────────────────────────────────────────────────────────

function MapAutoFit({ points }) {
  const map = useMap();
  useEffect(() => {
    if (points.length > 1) {
      const bounds = L.latLngBounds(points.map((p) => [p[0], p[1]]));
      map.fitBounds(bounds, { padding: [60, 60] });
    }
  }, [points, map]);
  return null;
}

function Field({ label, children }) {
  return (
    <div>
      <label style={{ fontSize: "0.62rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "6px" }}>
        {label}
      </label>
      {children}
    </div>
  );
}

function TextInput({ value, onChange, placeholder, type = "text", ...rest }) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      style={{
        width: "100%", padding: "10px 12px", borderRadius: "8px",
        background: "rgba(15,23,42,0.8)", border: "1px solid var(--border-color)",
        color: "#fff", fontSize: "0.8rem", outline: "none", boxSizing: "border-box",
      }}
      {...rest}
    />
  );
}

// ── Trip Details ──────────────────────────────────────────────────────────────

function TripDetails({ result, origin, destination }) {
  if (!result) return null;

  const rec = result.recommendation;
  const station = rec?.station;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

      {/* Status banner */}
      <div style={{
        padding: "14px", borderRadius: "10px",
        background: result.feasible ? "rgba(16,185,129,0.08)" : "rgba(239,68,68,0.08)",
        border: `1px solid ${result.feasible ? "var(--success)" : "var(--danger)"}`,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "6px" }}>
          {result.feasible
            ? <CheckCircle size={15} color="var(--success)" />
            : <AlertTriangle size={15} color="var(--danger)" />}
          <span style={{ fontWeight: "700", color: result.feasible ? "var(--success)" : "var(--danger)", fontSize: "0.78rem" }}>
            {result.feasible ? "TRIP FEASIBLE" : "CHARGING STOP REQUIRED"}
          </span>
        </div>
        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", lineHeight: "1.6" }}>{result.message}</p>
      </div>

      {/* ── Trip route summary (itinerary style) ── */}
      <div style={{ background: "rgba(15,23,42,0.5)", border: "1px solid var(--border-color)", borderRadius: "10px", padding: "14px" }}>
        <div style={{ fontSize: "0.65rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
          <Route size={12} /> TRIP ITINERARY
        </div>

        {/* Step: Origin */}
        <ItineraryStep
          dotColor="#3b82f6"
          label="START"
          title={origin}
          sub={`Battery: ${result.available_range?.toFixed(1)} km range available`}
          showLine={true}
          lineColor={station ? "#16a34a" : "#16a34a"}
        />

        {/* Step: Charging stop (if needed) */}
        {station && (
          <ItineraryStep
            dotColor="#16a34a"
            label="CHARGE"
            title={station.name}
            sub={`${rec.detour_km?.toFixed(1)} km detour — charge for ~${Math.round(rec.charging_time_mins)} min (${rec.strategy === "full" ? "Full charge" : "Minimum charge"})`}
            coords={`${station.lat.toFixed(5)}, ${station.lon.toFixed(5)}`}
            showLine={true}
            lineColor="#06b6d4"
            highlight={true}
          />
        )}

        {/* Step: Destination */}
        <ItineraryStep
          dotColor="#ef4444"
          label="ARRIVE"
          title={destination}
          sub={`${result.dest_distance?.toFixed(1)} km from origin`}
          showLine={false}
        />
      </div>

      {/* ── Metrics grid ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
        {[
          { label: "Available Range", val: `${result.available_range?.toFixed(1)} km`, color: "var(--accent)" },
          { label: "Trip Distance", val: `${result.dest_distance?.toFixed(1)} km`, color: "#fff" },
          { label: "Required (+10%)", val: `${result.required_range?.toFixed(1)} km`, color: result.feasible ? "var(--success)" : "var(--danger)" },
          station
            ? { label: "Wait (ML)", val: rec.queue_mins ? `${rec.queue_mins.toFixed(0)} min` : "0 min", color: "var(--accent)" }
            : { label: "Margin", val: `+${(result.available_range - result.required_range)?.toFixed(1)} km`, color: "var(--success)" },
        ].map((m) => (
          <div key={m.label} style={{ padding: "10px", background: "rgba(15,23,42,0.5)", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
            <div style={{ fontSize: "0.58rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "4px" }}>{m.label}</div>
            <div style={{ fontSize: "0.95rem", fontWeight: "700", color: m.color }}>{m.val}</div>
          </div>
        ))}
      </div>

      {/* ── Nearest vs Best Comparison ── */}
      {station && (
        <div style={{ padding: "12px", background: "rgba(6,182,212,0.05)", border: "1px solid rgba(6,182,212,0.2)", borderRadius: "10px" }}>
          <div style={{ fontSize: "0.6rem", fontWeight: "700", color: "var(--accent)", textTransform: "uppercase", marginBottom: "10px" }}>AI Optimization Impact</div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.72rem" }}>
            <div style={{ color: "var(--text-muted)" }}>
              Nearest Station:<br/>
              <span style={{ color: "#fff", fontWeight: "700" }}>~{Math.round(rec.charging_time_mins + rec.detour_km * 2 + 25)} min</span>
            </div>
            <div style={{ textAlign: "right" }}>
              VoltGrid Best:<br/>
              <span style={{ color: "var(--success)", fontWeight: "700" }}>~{Math.round(rec.charging_time_mins + rec.detour_km * 2 + (rec.queue_mins || 0))} min</span>
            </div>
          </div>
          <div style={{ marginTop: "8px", fontSize: "0.65rem", color: "var(--success)", textAlign: "center", background: "rgba(16,185,129,0.1)", padding: "4px", borderRadius: "4px" }}>
            💡 AI saved you {Math.round(25 - (rec.queue_mins || 0))} minutes by avoiding congestion
          </div>
        </div>
      )}

      {/* ── Station detail card ── */}
      {station && (
        <div style={{ padding: "14px", background: "rgba(22,163,74,0.06)", border: "1px solid #16a34a", borderRadius: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "10px" }}>
            <Zap size={14} color="#16a34a" />
            <span style={{ fontWeight: "700", color: "#16a34a", fontSize: "0.75rem" }}>CHARGING STATION DETAILS</span>
          </div>
          <div style={{ fontSize: "0.88rem", fontWeight: "700", marginBottom: "12px" }}>{station.name}</div>

          {/* Why this station was placed here (MCLP algorithm) */}
          <div style={{ marginBottom: "12px" }}>
            <div style={{ fontSize: "0.62rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "6px" }}>
              Why this location was chosen
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              {[
                {
                  icon: "⚡",
                  title: "Optimal Route Match",
                  desc: `Provides the shortest detour (+${rec.detour_km?.toFixed(1)} km) for your trip, saving time compared to alternative stations.`
                }
              ].map((item) => (
                <div key={item.title} style={{ padding: "9px 10px", background: "rgba(15,23,42,0.5)", borderRadius: "6px", border: "1px solid var(--border-color)" }}>
                  <div style={{ fontSize: "0.7rem", fontWeight: "700", color: "#16a34a", marginBottom: "3px" }}>
                    {item.icon} {item.title}
                  </div>
                  <div style={{ fontSize: "0.67rem", color: "var(--text-muted)", lineHeight: "1.6" }}>
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trip stats */}
          <div style={{ display: "flex", flexDirection: "column", gap: "5px", fontSize: "0.72rem", color: "var(--text-muted)", borderTop: "1px solid var(--border-color)", paddingTop: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Clock size={11} color="var(--accent)" />
              Charge time: <span style={{ color: "var(--accent)", fontWeight: "700", marginLeft: "4px" }}>~{Math.round(rec.charging_time_mins)} min</span>
              <span style={{ marginLeft: "4px" }}>({rec.strategy === "full" ? "Full charge" : "Minimum to complete trip"})</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Route size={11} color="var(--warning)" />
              Detour: <span style={{ color: "var(--warning)", fontWeight: "700", marginLeft: "4px" }}>+{rec.detour_km?.toFixed(1)} km</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <Navigation size={11} color="#fff" />
              Total route: <span style={{ color: "#fff", fontWeight: "700", marginLeft: "4px" }}>{rec.total_km?.toFixed(1)} km</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ItineraryStep({ dotColor, label, title, sub, coords, showLine, lineColor, highlight }) {
  return (
    <div style={{ display: "flex", gap: "12px" }}>
      {/* Dot + line */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ width: "14px", height: "14px", borderRadius: "50%", background: dotColor, border: "2px solid rgba(255,255,255,0.3)", flexShrink: 0 }} />
        {showLine && (
          <div style={{ width: "2px", flex: 1, minHeight: "32px", background: lineColor, opacity: 0.5, margin: "4px 0" }} />
        )}
      </div>
      {/* Text */}
      <div style={{ paddingBottom: showLine ? "12px" : 0, flex: 1 }}>
        <div style={{ fontSize: "0.58rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "2px" }}>{label}</div>
        <div style={{ fontSize: "0.82rem", fontWeight: "700", color: highlight ? "#16a34a" : "#fff", marginBottom: "3px" }}>{title}</div>
        <div style={{ fontSize: "0.68rem", color: "var(--text-muted)" }}>{sub}</div>
        {coords && <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontFamily: "monospace", marginTop: "2px" }}>{coords}</div>}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────

export default function DriverApp() {
  const [form, setForm] = useState({
    origin: "Andheri West, Mumbai",
    destination: "Bandra Kurla Complex, Mumbai",
    battery: 10,
    vehicleRange: 300,
    strategy: "full",
    use_ai: true,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [stations, setStations] = useState([]);

  useEffect(() => {
    fetch(`/api/stations?use_ai=${form.use_ai}`)
      .then((r) => r.json())
      .then((d) => setStations(d.stations || []));
  }, [form.use_ai]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const resp = await fetch("/api/route-check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          battery_pct: parseFloat(form.battery),
          vehicle_range_km: parseFloat(form.vehicleRange),
          origin: form.origin,
          destination: form.destination,
          strategy: form.strategy,
          use_ai: form.use_ai,
        }),
      });
      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      setResult(await resp.json());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const mapPoints = [];
  if (result?.origin_coords) mapPoints.push(result.origin_coords);
  if (result?.dest_coords) mapPoints.push(result.dest_coords);
  if (result?.recommendation?.station) {
    const s = result.recommendation.station;
    mapPoints.push([s.lat, s.lon]);
  }

  const batteryColor = form.battery < 20 ? "#ef4444" : form.battery < 40 ? "#f59e0b" : "#10b981";

  return (
    <div style={{ display: "flex", height: "calc(100vh - 64px)", margin: "-24px" }}>

      {/* ── Left Panel ── */}
      <aside style={{
        width: "360px", background: "var(--bg-panel)",
        borderRight: "1px solid var(--border-color)",
        overflowY: "auto", padding: "24px",
        display: "flex", flexDirection: "column", gap: "16px", flexShrink: 0,
      }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
            <Navigation size={17} color="var(--accent)" />
            <h2 style={{ fontSize: "0.95rem", fontWeight: "700", letterSpacing: "0.05em" }}>EV ROUTE PLANNER</h2>
          </div>
          <p style={{ fontSize: "0.71rem", color: "var(--text-muted)", lineHeight: "1.6" }}>
            Enter your trip details to check feasibility. VoltGrid finds the best charging stop if needed.
          </p>
          <label style={{
            display: "flex",
            alignItems: "center",
            gap: "10px",
            background: "rgba(6, 182, 212, 0.1)",
            padding: "10px",
            borderRadius: "8px",
            fontSize: "0.75rem",
            fontWeight: "700",
            border: "1px solid rgba(6, 182, 212, 0.3)",
            cursor: "pointer",
            marginTop: "12px"
          }}>
            <input 
              type="checkbox" 
              checked={form.use_ai} 
              onChange={(e) => setForm({ ...form, use_ai: e.target.checked })}
              style={{ width: "16px", height: "16px", accentColor: "var(--accent)" }}
            />
            USE AI PREDICTIONS
          </label>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "13px" }}>
          <Field label="Origin">
            <TextInput value={form.origin} onChange={(v) => setForm({ ...form, origin: v })} placeholder="e.g. Andheri West, Mumbai" />
          </Field>
          <Field label="Destination">
            <TextInput value={form.destination} onChange={(v) => setForm({ ...form, destination: v })} placeholder="e.g. Bandra Kurla Complex, Mumbai" />
          </Field>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px" }}>
            <Field label="Battery %">
              <TextInput type="number" min="1" max="100" value={form.battery} onChange={(v) => setForm({ ...form, battery: v })} />
            </Field>
            <Field label="Range (km)">
              <TextInput type="number" min="50" max="1000" value={form.vehicleRange} onChange={(v) => setForm({ ...form, vehicleRange: v })} />
            </Field>
          </div>

          <div>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
              <span style={{ fontSize: "0.62rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase" }}>Battery Level</span>
              <span style={{ fontSize: "0.72rem", fontWeight: "700", color: batteryColor }}>{form.battery}%</span>
            </div>
            <input type="range" min="1" max="100" value={form.battery}
              onChange={(e) => setForm({ ...form, battery: e.target.value })}
              style={{ width: "100%", accentColor: batteryColor }}
            />
          </div>

          <div>
            <span style={{ fontSize: "0.62rem", fontWeight: "700", color: "var(--text-muted)", textTransform: "uppercase", display: "block", marginBottom: "8px" }}>Charging Strategy</span>
            <div style={{ display: "flex", gap: "8px" }}>
              {["full", "min"].map((s) => (
                <button key={s} type="button" onClick={() => setForm({ ...form, strategy: s })}
                  style={{
                    flex: 1, padding: "8px", borderRadius: "6px",
                    border: `1px solid ${form.strategy === s ? "var(--accent)" : "var(--border-color)"}`,
                    background: form.strategy === s ? "rgba(6,182,212,0.15)" : "transparent",
                    color: form.strategy === s ? "var(--accent)" : "var(--text-muted)",
                    fontWeight: "700", fontSize: "0.68rem", textTransform: "uppercase", cursor: "pointer",
                  }}
                >
                  {s === "full" ? "Full Charge" : "Min Charge"}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" disabled={loading} style={{
            width: "100%", padding: "13px", borderRadius: "8px", border: "none",
            background: loading ? "rgba(6,182,212,0.3)" : "var(--accent)",
            color: loading ? "var(--text-muted)" : "#0a0f1e",
            fontWeight: "700", fontSize: "0.82rem", textTransform: "uppercase",
            cursor: loading ? "not-allowed" : "pointer",
            display: "flex", alignItems: "center", justifyContent: "center", gap: "8px",
          }}>
            {loading
              ? <><Loader size={15} style={{ animation: "spin 1s linear infinite" }} /> Checking Route...</>
              : <><Navigation size={15} /> CHECK FEASIBILITY</>}
          </button>
        </form>

        {error && (
          <div style={{ padding: "12px", background: "rgba(239,68,68,0.1)", border: "1px solid var(--danger)", borderRadius: "8px", fontSize: "0.73rem", color: "var(--danger)" }}>
            {error}
          </div>
        )}

        <TripDetails result={result} origin={form.origin} destination={form.destination} />
      </aside>

      {/* ── Map ── */}
      <div style={{ flex: 1 }}>
        <MapContainer center={[19.055, 72.855]} zoom={12} style={{ height: "100%", width: "100%" }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
          />

          {mapPoints.length > 1 && <MapAutoFit points={mapPoints} />}

          {/* All VoltGrid stations */}
          {stations.map((s) => (
            <Marker key={s.id} position={[s.lat, s.lon]} icon={stationIcon}>
              <Popup><strong>{s.name}</strong><br />{s.lat.toFixed(5)}, {s.lon.toFixed(5)}</Popup>
            </Marker>
          ))}

          {/* Result markers */}
          {result?.origin_coords && (
            <Marker position={result.origin_coords} icon={originIcon}>
              <Popup>Origin: {form.origin}</Popup>
            </Marker>
          )}
          {result?.dest_coords && (
            <Marker position={result.dest_coords} icon={destIcon}>
              <Popup>Destination: {form.destination}</Popup>
            </Marker>
          )}
          {result?.recommendation?.station && (
            <Marker
              position={[result.recommendation.station.lat, result.recommendation.station.lon]}
              icon={stationIcon}
            >
              <Popup>
                <strong>{result.recommendation.station.name}</strong><br />
                Charging stop — ~{Math.round(result.recommendation.charging_time_mins)} min
              </Popup>
            </Marker>
          )}

          {/* Route geometry */}
          {result?.feasible && result.route_geometry && (
            <Polyline positions={result.route_geometry} pathOptions={{ color: "#16a34a", weight: 5, opacity: 0.9 }} />
          )}
          {!result?.feasible && result?.leg1_geometry && (
            <Polyline positions={result.leg1_geometry} pathOptions={{ color: "#16a34a", weight: 5, opacity: 0.9 }} />
          )}
          {!result?.feasible && result?.leg2_geometry && (
            <Polyline positions={result.leg2_geometry} pathOptions={{ color: "#06b6d4", weight: 5, opacity: 0.85, dashArray: "8 5" }} />
          )}
        </MapContainer>
      </div>
    </div>
  );
}
