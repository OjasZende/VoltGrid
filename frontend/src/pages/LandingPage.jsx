import { Link } from "react-router-dom";
import { Zap, Brain, Battery } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="landing-page">
      <section className="hero-section">
        <div className="hero-badge">MUMBAI EV INFRASTRUCTURE</div>
        <h1 className="hero-title">
          Power the Future of<br />
          <span>EV Mobility</span>
        </h1>
        <p className="hero-desc">
          AI-driven optimization for EV charging station placement across Mumbai. 
          Precision infrastructure planning powered by deep learning.
        </p>
        <div className="hero-btns">
          <Link to="/dashboard" className="btn-primary">Launch Dashboard</Link>
          <Link to="/map" className="btn-outline">View Station Map</Link>
        </div>
      </section>

      <section className="feature-cards-grid">
        <div className="feature-card">
          <div className="feature-icon-box" style={{ background: 'rgba(6, 182, 212, 0.1)', color: '#06b6d4' }}>
            <Zap size={20} />
          </div>
          <h3 style={{ marginBottom: '12px', fontSize: '1.1rem' }}>MCLP Optimization</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            Maximal Covering Location Problem algorithms ensure optimal spatial distribution of charging nodes, 
            maximizing accessibility while minimizing infrastructural redundancy.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon-box" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' }}>
            <Brain size={20} />
          </div>
          <h3 style={{ marginBottom: '12px', fontSize: '1.1rem' }}>Neural Demand</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            Predictive modeling using recurrent neural networks to forecast spatial-temporal EV charging demand 
            across Mumbai's complex urban grid.
          </p>
        </div>

        <div className="feature-card">
          <div className="feature-icon-box" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
            <Battery size={20} />
          </div>
          <h3 style={{ marginBottom: '12px', fontSize: '1.1rem' }}>Reinforcement RL</h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
            Dynamic pricing and load balancing driven by reinforcement learning agents to stabilize grid load 
            and optimize station revenue streams.
          </p>
        </div>
      </section>
    </div>
  );
}
