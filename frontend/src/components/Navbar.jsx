import { Link, useLocation } from 'react-router-dom';
import { Zap } from 'lucide-react';
import '../index.css';

export default function Navbar() {
  const location = useLocation();

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/" className="brand-link">
          <Zap size={24} className="text-accent" fill="#3b82f6" />
          <span className="brand-text">VoltGrid</span>
        </Link>
      </div>
      <div className="nav-links">
        <Link 
          to="/" 
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          Home
        </Link>
        <Link 
          to="/dashboard" 
          className={`nav-link ${location.pathname === '/dashboard' ? 'active' : ''}`}
        >
          Dashboard
        </Link>
      </div>
    </nav>
  );
}
