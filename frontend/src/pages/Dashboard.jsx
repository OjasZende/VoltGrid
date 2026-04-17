import { useState, useEffect } from "react";
import { Zap, Car, Map as MapIcon, Activity, Battery } from "lucide-react";
import "./dashboard_new.css";

export default function Dashboard() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));
  const [stationCount, setStationCount] = useState("...");
  const [currentSlide, setCurrentSlide] = useState(0);

  // Accurate Data specific to Mumbai EV Market (Dec 2024)
  const MUMBAI_TOTAL_EVS = "40,958";
  const MUMBAI_CARS = "12,000+";
  const MUMBAI_BIKES = "24,000+";

  const slides = [
    {
      title: "Maximized Demand Coverage",
      desc: "VoltGrid's MCLP algorithm ensures chargers are placed precisely in high-demand zones, minimizing range anxiety for over 40,000 registered EVs in Mumbai.",
      icon: <MapIcon size={48} className="slide-icon" />
    },
    {
      title: "Strategic Grid Placement",
      desc: "Our neural engine evaluates proximity to commercial POIs and electrical substations to prevent grid stress while aggressively meeting rising charging demands.",
      icon: <Zap size={48} className="slide-icon" />
    },
    {
      title: "Optimized Driver Routing",
      desc: "Integrated with OSRM road geometry to provide EV drivers with the absolute minimum detour paths for required charging stops along their route.",
      icon: <Car size={48} className="slide-icon" />
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Fetch actual active station count from backend
    fetch("/api/stations")
      .then(res => res.json())
      .then(data => {
        if (data.stations) {
          setStationCount(data.stations.length.toString());
        }
      })
      .catch(err => console.error("Error fetching stations:", err));
  }, []);

  useEffect(() => {
    // Slideshow auto-rotation
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [slides.length]);

  return (
    <div className="dashboard-page new-dashboard">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: '40px' }}>
        <div className="page-title-group">
          <h1 className="page-title">SYSTEM ANALYTICS</h1>
          <p className="page-subtitle">VOLTGRID PLANNING MODE</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.8rem', fontWeight: '700', color: 'var(--accent)', fontFamily: 'monospace' }}>{time} IST</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: '700', marginTop: '4px' }}>LIVE NETWORK STATUS</div>
        </div>
      </div>

      {/* Hero Slideshow Section */}
      <div className="slideshow-container">
        {slides.map((slide, index) => (
          <div 
            key={index} 
            className={`slide ${index === currentSlide ? "active" : ""}`}
          >
            <div className="slide-content">
              <div className="slide-icon-wrapper">{slide.icon}</div>
              <div className="slide-text">
                <h2>{slide.title}</h2>
                <p>{slide.desc}</p>
              </div>
            </div>
          </div>
        ))}
        
        {/* Slideshow Indicators */}
        <div className="slide-indicators">
          {slides.map((_, index) => (
            <div 
              key={index} 
              className={`indicator ${index === currentSlide ? "active" : ""}`}
              onClick={() => setCurrentSlide(index)}
            />
          ))}
        </div>
      </div>

      {/* Interactive Data Cards */}
      <div className="interactive-cards-grid">
        
        <div className="interactive-card">
          <div className="card-bg-glow" style={{ background: "radial-gradient(circle at top right, rgba(6, 182, 212, 0.15), transparent 70%)" }}></div>
          <div className="card-content">
            <div className="card-header">
              <Activity size={18} color="var(--accent)" />
              <span>ACTIVE INFRASTRUCTURE</span>
            </div>
            <div className="card-value">{stationCount}</div>
            <div className="card-subtext">Optimized VoltGrid Nodes Online</div>
          </div>
        </div>

        <div className="interactive-card">
          <div className="card-bg-glow" style={{ background: "radial-gradient(circle at top right, rgba(139, 92, 246, 0.15), transparent 70%)" }}></div>
          <div className="card-content">
            <div className="card-header">
              <Car size={18} color="#8b5cf6" />
              <span>MUMBAI EV FLEET</span>
            </div>
            <div className="card-value" style={{ color: "#8b5cf6" }}>{MUMBAI_TOTAL_EVS}</div>
            <div className="card-subtext">Total EVs Registered (As of Dec 2024)</div>
          </div>
        </div>

        <div className="interactive-card">
          <div className="card-bg-glow" style={{ background: "radial-gradient(circle at top right, rgba(16, 185, 129, 0.15), transparent 70%)" }}></div>
          <div className="card-content">
            <div className="card-header">
              <Battery size={18} color="#10b981" />
              <span>FLEET BREAKDOWN</span>
            </div>
            <div className="card-value" style={{ fontSize: "1.9rem", color: "#10b981" }}>
              {MUMBAI_CARS} <span style={{fontSize: "1rem", color: "var(--text-muted)", fontWeight: "normal"}}>Cars</span>
            </div>
            <div className="card-subtext" style={{ marginTop: "4px" }}>
              <strong style={{color: "#fff"}}>{MUMBAI_BIKES}</strong> Two-Wheelers
            </div>
          </div>
        </div>

      </div>

    </div>
  );
}
