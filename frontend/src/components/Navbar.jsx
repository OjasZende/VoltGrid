import { NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import { Clock, LayoutDashboard, Map as MapIcon, LineChart, Battery, Navigation } from "lucide-react";
import '../index.css';

export default function Navbar() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-US', { hour12: false }));

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString('en-US', { hour12: false }));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <span className="nav-brand-main">VoltGrid</span>
        <span className="nav-brand-sub">MUMBAI EV OPTIMIZER</span>
      </div>

      <div className="nav-links">
        <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          DASHBOARD
        </NavLink>
        <NavLink to="/map" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          STATION MAP
        </NavLink>
        <NavLink to="/demand" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          DEMAND FORECAST
        </NavLink>
        <NavLink to="/v2c" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          V2C MONITOR
        </NavLink>
        <NavLink to="/driver" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
          DRIVER APP
        </NavLink>
      </div>

      <div className="navbar-right">
        <div className="nav-time">
          <Clock size={14} style={{ marginRight: '6px', verticalAlign: 'middle' }} />
          {time} IST
        </div>
        <div className="live-badge">LIVE</div>
      </div>
    </nav>
  );
}
