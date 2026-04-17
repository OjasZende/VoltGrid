import { NavLink, Link, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Clock, LayoutDashboard, Map as MapIcon, LineChart, Battery, Navigation, ArrowRight } from "lucide-react";
import '../index.css';

export default function Navbar() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));
  const location = useLocation();

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const isCitizenMode = location.pathname === "/driver";

  return (
    <nav className="navbar">
      <Link to="/" className="nav-brand" style={{ textDecoration: 'none' }}>
        <span className="nav-brand-main">VoltGrid</span>
        <span className="nav-brand-sub">MUMBAI EV OPTIMIZER</span>
      </Link>

      <div className="nav-links">
        {isCitizenMode ? (
          <NavLink to="/driver" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            DRIVER APP (CITIZEN MODE)
          </NavLink>
        ) : (
          <>
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              DASHBOARD
            </NavLink>
            <NavLink to="/map" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              STATION MAP
            </NavLink>
            <NavLink to="/demand" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              DEMAND FORECAST
            </NavLink>
          </>
        )}
      </div>

      <div className="navbar-right">
        {isCitizenMode ? (
          <Link to="/dashboard" className="mode-switcher-btn" style={{ marginRight: '16px' }}>
            Switch to Planning Mode <ArrowRight size={14} style={{ marginLeft: '4px' }} />
          </Link>
        ) : (
          <Link to="/driver" className="mode-switcher-btn" style={{ marginRight: '16px' }}>
            Switch to Citizen Mode <ArrowRight size={14} style={{ marginLeft: '4px' }} />
          </Link>
        )}
        
        <div className="nav-time">
          <Clock size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
          {time} IST
        </div>
        <div className="live-badge">LIVE</div>
      </div>
    </nav>
  );
}
