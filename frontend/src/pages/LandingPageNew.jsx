import { useState } from "react";
import { Link } from "react-router-dom";
import { Car, BarChart2, Zap, Trophy, MousePointerClick } from "lucide-react";
import "./landing_new.css";

// --- Grid Master Minigame Component ---
function GridMasterGame() {
  const [chargers, setChargers] = useState([]);
  const [score, setScore] = useState(null);

  // Fixed positions for cars on a 5x5 grid (0-4 index)
  const cars = [
    { id: 1, x: 1, y: 1 },
    { id: 2, x: 3, y: 1 },
    { id: 3, x: 2, y: 3 },
    { id: 4, x: 0, y: 4 },
  ];

  const maxChargers = 2;
  const coverageRadius = 1.5; // distance (Euclidean or Manhattan)

  const handleGridClick = (x, y) => {
    // If clicking a charger, remove it
    const existingIdx = chargers.findIndex(c => c.x === x && c.y === y);
    if (existingIdx !== -1) {
      setChargers(chargers.filter((_, i) => i !== existingIdx));
      setScore(null);
      return;
    }
    
    // If clicking a car, ignore
    if (cars.some(c => c.x === x && c.y === y)) return;

    // Place a new charger if under limit
    if (chargers.length < maxChargers) {
      setChargers([...chargers, { x, y }]);
      setScore(null);
    }
  };

  const checkScore = () => {
    let covered = 0;
    cars.forEach(car => {
      let isCovered = false;
      chargers.forEach(charger => {
        // Manhattan distance
        const dist = Math.abs(car.x - charger.x) + Math.abs(car.y - charger.y);
        if (dist <= coverageRadius) isCovered = true;
      });
      if (isCovered) covered++;
    });
    setScore((covered / cars.length) * 100);
  };

  const resetGame = () => {
    setChargers([]);
    setScore(null);
  };

  return (
    <div className="minigame-container">
      <div className="minigame-header">
        <h3 style={{ margin: 0, display: "flex", alignItems: "center", gap: "8px" }}><Zap size={18} color="var(--accent)"/> Grid Master Challenge</h3>
        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", margin: "4px 0 0 0" }}>
          Place {maxChargers} chargers to cover as many EVs as possible. (Click to place)
        </p>
      </div>

      <div style={{ display: "flex", gap: "24px", marginTop: "16px", alignItems: "flex-start" }}>
        {/* Game Board */}
        <div className="game-board">
          {[...Array(5)].map((_, y) => (
            <div key={`row-${y}`} style={{ display: "flex" }}>
              {[...Array(5)].map((_, x) => {
                const isCar = cars.some(c => c.x === x && c.y === y);
                const isCharger = chargers.some(c => c.x === x && c.y === y);
                
                // Show coverage highlight if score was checked
                let isCovered = false;
                if (score !== null && !isCharger && !isCar) {
                  chargers.forEach(charger => {
                    const dist = Math.abs(x - charger.x) + Math.abs(y - charger.y);
                    if (dist <= coverageRadius) isCovered = true;
                  });
                }

                return (
                  <div 
                    key={`cell-${x}-${y}`} 
                    className={`game-cell ${isCharger ? "has-charger" : ""} ${isCovered ? "is-covered" : ""}`}
                    onClick={() => handleGridClick(x, y)}
                  >
                    {isCar && <Car size={20} color="#3b82f6" />}
                    {isCharger && <Zap size={20} color="#10b981" fill="#10b981" />}
                  </div>
                );
              })}
            </div>
          ))}
        </div>

        {/* Game Stats & Controls */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "12px" }}>
          <div className="game-stat-box">
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: "700" }}>Chargers Used</div>
            <div style={{ fontSize: "1.2rem", fontWeight: "700", color: chargers.length === maxChargers ? "var(--warning)" : "white" }}>
              {chargers.length} / {maxChargers}
            </div>
          </div>
          
          <button 
            className="game-btn primary" 
            onClick={checkScore}
            disabled={chargers.length === 0}
          >
            <MousePointerClick size={16} /> Test Coverage
          </button>
          
          <button className="game-btn outline" onClick={resetGame}>
            Reset Board
          </button>

          {score !== null && (
            <div className={`game-result-box ${score === 100 ? "perfect" : ""}`}>
              {score === 100 ? <Trophy size={20} color="#fbbf24" /> : <BarChart2 size={20} />}
              <div>
                <div style={{ fontWeight: "700", fontSize: "1.1rem" }}>{score}% Coverage</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.8 }}>
                  {score === 100 ? "Perfect placement!" : "You can do better. Try again!"}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// --- Main Landing Page Component ---
export default function LandingPageNew() {
  return (
    <div className="landing-page-new">
      <div className="hero-section-new">
        <div className="hero-badge-new">WELCOME TO VOLTGRID</div>
        <h1 className="hero-title-new">Smart Charging for Everyone</h1>
        <p className="hero-desc-new">
          VoltGrid is a data-driven system that ensures EV chargers are placed exactly where they are needed, based on real-world demand.
        </p>
      </div>

      {/* Mode Selector */}
      <div className="mode-selector-container">
        <Link to="/driver" className="mode-card driver-mode">
          <div className="mode-icon"><Car size={32} /></div>
          <h2>Citizen Mode</h2>
          <p>I'm an EV driver looking for the smartest route and nearest charging station.</p>
          <div className="mode-btn">Launch Driver App →</div>
        </Link>

        <Link to="/dashboard" className="mode-card planner-mode">
          <div className="mode-icon"><BarChart2 size={32} /></div>
          <h2>Planning Mode</h2>
          <p>I'm an infrastructure planner analyzing grid stress and optimal charger placement.</p>
          <div className="mode-btn">Launch Analytics Dashboard →</div>
        </Link>
      </div>

      {/* Educational Minigame Section */}
      <div style={{ maxWidth: "800px", margin: "40px auto", padding: "0 20px" }}>
        <GridMasterGame />
      </div>

    </div>
  );
}
