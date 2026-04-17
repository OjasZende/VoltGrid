# VoltGrid — Complete Project Explanation

> A complete technical walkthrough of the VoltGrid EV charging station optimizer for Mumbai.
> Share this with teammates to get everyone up to speed quickly.

---

## What is VoltGrid?

**VoltGrid** is an intelligent EV (Electric Vehicle) charging station placement tool for **Mumbai**. It uses real map data, mathematical optimization, and AI/neural networks to answer one question:

> *"Given a limited budget of N charging stations, where exactly should they be placed in Mumbai to serve the maximum number of people?"*

---

## Project Structure

```
VoltGrid-1/
├── app.py                         ← Python backend server (FastAPI)
├── data/
│   └── mumbai_network.graphml     ← Real Mumbai road network
├── backend/algo/
│   ├── extraction_script.py       ← Step 1: Get map data from OSM
│   ├── distance_matrix.py         ← Step 2: Calculate travel times
│   └── set_cover_optimizer.py     ← Step 3: Solve the math problem (MCLP)
└── frontend/src/
    ├── App.jsx                    ← Router / navigation hub
    ├── pages/
    │   ├── LandingPage.jsx        ← Home screen
    │   ├── Dashboard.jsx          ← Overview stats page
    │   ├── StationMap.jsx         ← Interactive map (core feature)
    │   ├── DemandForecast.jsx     ← Neural net demand prediction
    │   └── V2CMonitor.jsx         ← Reinforcement Learning agent
    └── components/
        └── Navbar.jsx             ← Top navigation bar
```

---

## How to Run

### Backend (Python)
```bash
# From the project root:
python app.py
# Server starts at http://localhost:8000
# Auto-loads Mumbai map data on startup (takes ~1-2 minutes first time)
```

### Frontend (React)
```bash
cd frontend
npm install --legacy-peer-deps   # only needed first time
npm run dev
# App opens at http://localhost:5173
```

> **Both must be running** for the Station Map to work. The other pages (Dashboard, Demand Forecast, V2C Monitor) work without the backend.

---

## THE BACKEND (Python)

### Step 1 — `extraction_script.py` — Getting Real Mumbai Data

Uses **OSMnx** (OpenStreetMap library) to download real geographic data.

```
Mumbai map bounding box
    ↓
Fetches "power: substation" nodes → Candidate Sites (where a charger COULD go) — 50 sites
    ↓
Divides area into H3 Hexagons (resolution 9) → Demand Points (zones where people live) — 376 zones
    ↓
Fetches POIs (shops, malls, transit stops) → Used to WEIGHT each hexagon
    ↓
Returns: 50 candidate sites, 376 demand points, weights dict, substation coordinates
```

**Why hexagons?**
Uber's H3 library divides any map into equal hexagonal cells. Each hexagon = one "zone of demand". Hexagons tile perfectly with no gaps, unlike squares.

**Why weight demand by POIs?**
A hexagon containing a shopping mall + bus stop is more valuable to cover than an empty residential street. The weight = number of nearby Points of Interest in that zone.

---

### Step 2 — `distance_matrix.py` — Travel Time Calculations

Answers: *"Which candidate stations can actually reach which demand zones within 10 minutes?"*

```python
# Loads the real Mumbai road graph (every street, every junction)
G = ox.load_graphml("mumbai_network.graphml")

# For EVERY road edge, calculates travel time:
# time (seconds) = (length in km) / (speed in km/h) × 3600
# Speed comes from OSM's maxspeed tag, or falls back to road-type defaults
# PEAK HOUR MULTIPLIER = 0.5 → halves all speeds (simulates peak congestion)

# Dijkstra's shortest-path algorithm runs from each demand point
# Cutoff = 600 seconds (10 minutes peak-hour driving)

# Result:
reachability_map = {
    demand_idx: [list of reachable candidate station indices]
}
```

**What is Dijkstra's algorithm?**
It's the same algorithm GPS navigation uses. Starting from one point, it finds the shortest (fastest) path to every other point in the road network. Here it finds every charging station reachable within 10 minutes from each demand zone.

---

### Step 3 — `set_cover_optimizer.py` — The Math Optimization (MCLP)

Solves the **Maximal Covering Location Problem** — a classic operations research problem:

```
Given:
  50 candidate sites
  376 demand zones (each with a population weight)
  Budget K (e.g., K=10 stations)
  Reachability map (who can reach who within 10 min)

Find:
  Which K sites to select so that the total weighted demand covered is MAXIMIZED
```

**Formulation solved by Pyomo + GLPK solver:**

```
Variables:
  x[j] = 1 if we place a station at candidate j, else 0
  y[i] = 1 if demand zone i is covered, else 0

Maximize:
  sum of (weight[i] × y[i])           ← maximize covered weighted demand

Subject to:
  sum of x[j] ≤ K                     ← cannot exceed budget
  y[i] ≤ sum of x[j] for j in N(i)   ← zone only covered if a station reaches it
  sum of x[j] ≤ 1 per substation      ← grid congestion: max 1 station per 1km of substation
```

**GLPK** is a Mixed-Integer Linear Programming solver. It systematically explores combinations of station placements to find the mathematically guaranteed optimal solution.

---

### `app.py` — FastAPI Web Server (Port 8000)

The bridge between Python and React. Exposes two REST API endpoints:

| Endpoint | What it does |
|---|---|
| `GET /api/spatial-data` | Returns candidate sites, demand hexagons, weights |
| `GET /api/optimize?k=10` | Runs the MCLP solver, returns optimal station coordinates |

On startup, it pre-loads all spatial data so API calls are fast.

---

## THE FRONTEND (React + Vite)

### Navigation — `App.jsx` + `Navbar.jsx`

Uses **React Router** to manage 5 pages without full page reloads:

| URL | Page |
|---|---|
| `/` | Landing Page (no navbar) |
| `/dashboard` | Overview Dashboard |
| `/map` | Interactive Station Map |
| `/demand` | Demand Forecast (Neural Net) |
| `/v2c` | V2C Monitor (RL Agent) |

---

## Page-by-Page Explanation

### 🏠 Landing Page (`/`)
Marketing-style entry page with hero section, feature highlights, and a "Launch Dashboard" button. Pure UI — no data fetching.

---

### 📊 Dashboard (`/dashboard`)

Real-time overview with simulated live metrics:
- **4 Stat Cards**: Total Stations (500), EVs Covered (10,00,000), Grid Stress Saved (34%), Active V2C Nodes (1,240)
- **Demand Curve**: SVG line chart of simulated hourly electricity demand across 24 hours. Drifts slightly every 5 seconds to feel live.
- **Station Status Donut**: Hand-drawn SVG donut (no library) showing Available / Busy / Overcrowded / Offline proportions.

---

### 🗺️ Station Map (`/map`) — THE CORE FEATURE

This is where the real optimization happens:

```
Page loads
    ↓
React calls GET /api/spatial-data
    ↓
Receives 50 candidate sites + 376 hexagon polygons + weights
    ↓
Renders on Leaflet map (dark CartoDB tile layer)
    ↓
User moves slider (K = budget, 1–30)
    ↓
React calls GET /api/optimize?k=K
    ↓
Python runs MCLP solver (GLPK)
    ↓
Returns optimal station coordinates as JSON
    ↓
Map updates: green bolt icons = selected, grey dots = rejected
    ↓
Green circles show coverage radius of each selected station
```

**"Before" tab**: All 50 candidates shown as red dots.
**"After" tab**: Only the K optimal stations as green bolt icons + coverage circles.

**Hexagon color heatmap**: Each hexagon is colored by its POI weight. Brighter orange/red = higher demand.

**Neural Placement Engine (sidebar panel):**
- Click "Optimize All Stations" to run a TF.js neural network (10→8→1, sigmoid)
- Each site gets 5 random feature inputs (EV density, grid capacity, traffic, existing coverage, population density)
- Markers flash yellow while being analyzed
- Top 5 stations shown in a bar chart by neural score
- Toast notification confirms completion

---

### 🧠 Demand Forecast (`/demand`) — Neural Network Feature

**Canvas Neural Network Diagram:**

The diagram is drawn manually using the HTML5 Canvas API (no image files):
- Input Layer: 5 nodes (Hour, Day, Temp, Traffic, EV Count)
- Hidden Layer 1: 8 nodes (purple)
- Hidden Layer 2: 6 nodes (purple)
- Output Layer: 1 node — "MW Demand" (green)

Every 4 seconds:
1. Random inputs are generated (realistic Mumbai ranges)
2. TensorFlow.js model runs `model.predict(tensor)`
3. Output × 800 = MW prediction (e.g., 487 MW)
4. Canvas animates: each layer's nodes glow, connections fire cyan left→right
5. Input values update, confidence score updates, sparkline shifts

**The TF.js model:**
```javascript
const model = tf.sequential();
model.add(tf.layers.dense({inputShape: [5], units: 8, activation: 'relu'}));
model.add(tf.layers.dense({units: 6, activation: 'relu'}));
model.add(tf.layers.dense({units: 1, activation: 'linear'}));
```
This is a randomly initialized feedforward neural network. In a real deployment, it would be trained on historical Mumbai electricity demand data.

**ReLU activation**: Outputs max(0, x) — introduces non-linearity so the network can learn complex patterns.

---

### 🔋 V2C Monitor (`/v2c`) — Reinforcement Learning Feature

**V2C = Vehicle-to-Grid**: EVs can send power BACK to the grid during peak demand.

**The RL Agent is a real Q-Learning implementation:**

```
Q-Table: 3 states × 3 actions = 9 learnable values

States:  Low Stress | Medium Stress | High Stress
Actions: Activate V2C | Hold | Deactivate V2C

Every 5 seconds:
1. Read current grid stress level (state s)
2. Pick action using ε-greedy:
     15% chance: pick random action (exploration)
     85% chance: pick action with highest Q-value (exploitation)
3. Apply action → stress level changes
4. Calculate reward:
     Activate and stress drops  → +10
     Hold stable                → +2
     Stress increases           → -5
5. Update Q-value using Bellman equation:
     Q[s][a] = Q[s][a] + α × (reward + γ × max(Q[next_s]) - Q[s][a])
     α = 0.1  (learning rate — how fast to update)
     γ = 0.9  (discount factor — value of future rewards)
```

**What you see:**
- **Q-Table grid**: 9 Q-values updating live. The chosen action cell glows cyan.
- **Learning curve SVG**: Cumulative reward trends upward as the agent learns better policies.
- **Decision Log**: Last 6 decisions with timestamp, state, action taken, and reward earned.

The reward curve trends upward because the agent gradually learns that "Activate V2C when High Stress" and "Deactivate when Low Stress" consistently earn better rewards.

---

## How Everything Connects

```
Browser (localhost:5173)
    ↓
React app renders UI, user interacts with map
    ↓
Fetch calls to localhost:8000 (Python backend)
    ↓
FastAPI receives request
    ↓
Runs: extraction → distance matrix → MCLP optimization
    ↓
GLPK solver finds mathematically optimal station placement
    ↓
Returns JSON with coordinates
    ↓
React renders stations as markers on Leaflet map
```

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Road network | OSMnx | Real Mumbai streets from OpenStreetMap |
| Hexagonal grid | Uber H3 | Equal-area demand zones |
| Optimization | Pyomo + GLPK | Solves integer linear programs exactly |
| Backend API | FastAPI (Python) | Fast REST API server |
| Frontend | React 18 + Vite | Component-based UI, fast hot-reload |
| Map rendering | React-Leaflet | Interactive maps in React |
| Neural networks | TensorFlow.js (CDN) | ML models running in the browser |
| Routing | React Router v6 | Multi-page navigation without reloads |
| Styling | Pure CSS | Custom dark glassmorphism theme |
| Solver | GLPK (winglpk) | Free open-source LP/MIP solver |

---

## Key Algorithms Summary

| Algorithm | Where Used | What it Does |
|---|---|---|
| Dijkstra's Shortest Path | `distance_matrix.py` | Finds all stations reachable within 10 min from each demand zone |
| MCLP (Integer Programming) | `set_cover_optimizer.py` | Selects the K optimal station locations |
| H3 Hexagonal Binning | `extraction_script.py` | Divides Mumbai into equal demand zones |
| Feedforward Neural Network | `DemandForecast.jsx` | Predicts electricity demand in MW |
| Q-Learning (RL) | `V2CMonitor.jsx` | Learns when to activate/deactivate V2C |
| Haversine Distance | `set_cover_optimizer.py` | Great-circle distance between GPS coordinates |

---

*Generated by VoltGrid — Mumbai EV Charging Station Optimizer*
