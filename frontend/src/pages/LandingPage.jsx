import { Link } from 'react-router-dom';
import { Zap, Map, Activity, ShieldCheck } from 'lucide-react';
import '../index.css';

export default function LandingPage() {
  return (
    <div className="landing-page">
      <div className="hero-section">
        <div className="hero-content">
          <div className="badge">
            <Zap size={16} /> <span>Powered by MCLP Algorithms</span>
          </div>
          <h1 className="hero-title">
            Optimizing Mumbai's <br />
            <span className="text-accent">EV Infrastructure</span>
          </h1>
          <p className="hero-subtitle">
            Deploy charging stations with mathematical precision. Our platform uses H3 Hexagons and the Maximal Covering Location Problem (MCLP) to maximize EV charging accessibility across the city.
          </p>
          <div className="hero-actions">
            <Link to="/dashboard" className="btn btn-primary">
              Launch Dashboard
            </Link>
            <a href="#features" className="btn btn-secondary">
              Learn More
            </a>
          </div>
        </div>
        <div className="hero-visual">
          <div className="glow-circle"></div>
          <div className="glass-card mockup-card">
            <div className="mockup-header">
              <div className="dots">
                <span className="dot dot-r"></span>
                <span className="dot dot-y"></span>
                <span className="dot dot-g"></span>
              </div>
              <div className="mockup-title">VoltGrid Optimizer</div>
            </div>
            <div className="mockup-body">
              <div className="mockup-map">
                {/* Abstract visualization of a map grid */}
                <div className="abstract-hex-grid">
                  {[...Array(7)].map((_, i) => (
                    <div key={i} className={`abstract-hex hex-${i}`}></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section id="features" className="features-section">
        <h2 className="section-title">Why VoltGrid?</h2>
        <div className="features-grid">
          <div className="feature-card">
            <div className="feature-icon"><Map size={32} /></div>
            <h3>H3 Hexagon Grids</h3>
            <p>We partition the city into high-resolution Uber H3 hexagons to precisely model demand and charging POIs.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><Activity size={32} /></div>
            <h3>MCLP Solver</h3>
            <p>Our backend leverages GLPK to solve the Maximal Covering Location Problem, finding the mathematically optimal station placements.</p>
          </div>
          <div className="feature-card">
            <div className="feature-icon"><ShieldCheck size={32} /></div>
            <h3>Data-Driven Insights</h3>
            <p>Every decision is backed by real POI data (retail, transit, commercial) extracted from OpenStreetMap.</p>
          </div>
        </div>
      </section>
    </div>
  );
}
