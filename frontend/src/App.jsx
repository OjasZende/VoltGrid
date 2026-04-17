import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import LeftSidebar from './components/LeftSidebar';
import LandingPage from './pages/LandingPage';
import Dashboard from './pages/Dashboard';
import StationMap from './pages/StationMap';
import DemandForecast from './pages/DemandForecast';
import V2CMonitor from './pages/V2CMonitor';
import DriverApp from './pages/DriverApp';
import './index.css';

function AppContent() {
  const location = useLocation();
  const isLanding = location.pathname === "/";
  // Demand, V2C, and DriverApp use the left vertical sidebar layout
  const isSidebarLayout = ["/demand", "/v2c", "/driver"].includes(location.pathname);

  return (
    <div className="app-container">
      {/* Top Navbar for everything except Landing and Sidebar-layout pages */}
      {!isLanding && !isSidebarLayout && <Navbar />}
      
      <div className="main-content">
        {isSidebarLayout && <LeftSidebar />}
        <main className={isSidebarLayout ? "main-content-area sidebar-view" : "main-content-area"}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/map" element={<StationMap />} />
            <Route path="/demand" element={<DemandForecast />} />
            <Route path="/v2c" element={<V2CMonitor />} />
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
