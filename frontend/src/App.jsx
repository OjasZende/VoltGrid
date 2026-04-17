import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import LandingPageNew from './pages/LandingPageNew';
import Dashboard from './pages/Dashboard';
import StationMap from './pages/StationMap';
import DemandForecast from './pages/DemandForecast';
import DriverApp from './pages/DriverApp';
import './index.css';

function AppContent() {
  const location = useLocation();
  const isLanding = location.pathname === "/";

  return (
    <div className="app-container">
      {/* Top Navbar for everything except Landing */}
      {!isLanding && <Navbar />}
      
      <div className="main-content">
        <main className="main-content-area">
          <Routes>
            <Route path="/" element={<LandingPageNew />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map" element={<StationMap />} />
            <Route path="/demand" element={<DemandForecast />} />
            <Route path="/driver" element={<DriverApp />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
