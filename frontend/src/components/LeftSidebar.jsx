import { NavLink } from "react-router-dom";
import { LayoutDashboard, Map as MapIcon, LineChart, Battery, Navigation } from "lucide-react";

export default function LeftSidebar() {
  return (
    <aside className="left-sidebar">
      <div className="sidebar-logo">
        <div className="nav-brand-main">VoltGrid</div>
        <div className="nav-brand-sub">MUMBAI EV OPTIMIZER</div>
      </div>
      
      <nav className="sidebar-links">
        <NavLink to="/dashboard" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <LayoutDashboard size={18} />
          DASHBOARD
        </NavLink>
        <NavLink to="/map" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <MapIcon size={18} />
          MAP
        </NavLink>
        <NavLink to="/demand" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <LineChart size={18} />
          FORECAST
        </NavLink>
        <NavLink to="/v2c" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Battery size={18} />
          MONITOR
        </NavLink>
        <NavLink to="/driver" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
          <Navigation size={18} />
          DRIVER APP
        </NavLink>
      </nav>
    </aside>
  );
}
