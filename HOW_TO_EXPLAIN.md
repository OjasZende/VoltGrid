# VoltGrid — How to Explain This Project

> A simple, clear guide for presenting VoltGrid to teammates, judges, or professors.
> Read this top to bottom and you'll know exactly what to say.

---

## THE ONE-LINE PITCH

> "VoltGrid is an AI-powered system that tells you exactly where to place EV charging stations
> in Mumbai so that the maximum number of people can access them — using real map data,
> mathematical optimization, and machine learning."

---

## THE PROBLEM WE ARE SOLVING

Mumbai is one of the fastest-growing EV markets in India.
But charging infrastructure is placed poorly — stations are clustered in some areas
and completely absent in others.

**The challenge:** If the government or a company has a budget for, say, 10 new charging
stations — where exactly should they go to serve the most people?

This is harder than it sounds because:
- You can't just pick the 10 most populated spots (they might all be within 500m of each other)
- You have to consider road network, traffic, and driving time — not just straight-line distance
- The electrical grid has constraints — you can't overload a substation area

**VoltGrid solves this automatically.**

---

## HOW THE SYSTEM WORKS — 3 STEPS

```
STEP 1: Understand Mumbai          STEP 2: Calculate Reachability       STEP 3: Find Optimal Placement
=========================          ==============================        ==============================

Download real road network    -->  For each zone: which stations   -->  Run optimization algorithm:
from OpenStreetMap                 can reach it within 10 minutes?      "which K stations cover the
                                   (using actual driving time,           most weighted demand?"
Identify candidate sites:          peak-hour congestion = 0.5x
  Power substations (50 sites)     speed reduction)                 GLPK solver finds the
                                                                     mathematically guaranteed
Divide city into hexagonal         Build a reachability map:        best answer.
demand zones (376 zones)           demand[i] -> [station1, station5,
                                                station12, ...]     Output: coordinates of the
Measure demand weight per                                            optimal stations
zone using POI count:
  shops, malls, transit stops
```

---

## THE CORE ALGORITHM — MCLP (Maximal Covering Location Problem)

This is a classic Operations Research problem. The math:

```
We choose x[j] = 1 if we place a station at candidate site j, else 0
We define y[i] = 1 if demand zone i is covered, else 0

MAXIMIZE:   total weighted demand covered
            = sum of (weight[i] x y[i])  for all zones i

SUBJECT TO:
  sum of x[j] <= K                         (cannot exceed budget of K stations)
  y[i] <= sum of x[j] for all j in N(i)   (zone is only covered if a station can reach it)
  sum of x[j] <= 1 near each substation    (grid constraint: prevent overloading)
```

**In plain English:** Place at most K stations such that the total weighted population
that has at least one station within 10 minutes of driving is maximized.

Solved using GLPK — a professional-grade mathematical solver used in industry.

---

## THE DATA PIPELINE

```
OpenStreetMap (Real Mumbai Data)
        |
        |--> Road network graph (every street, junction, speed limit)
        |--> Power substation locations (candidate charging sites: 50 total)
        |--> Points of Interest: shops, malls, transit stops
        |
        v
extraction_script.py
        |
        |--> 50 candidate sites (lat/lon)
        |--> 376 H3 hexagonal demand zones (covering Mumbai)
        |--> Demand weights (POI count per hexagon)
        |--> Substation coordinates (for grid constraint)
        |
        v
distance_matrix.py
        |
        |--> Loads road graph
        |--> Assigns travel time to every road segment:
        |      time = (length / speed) x 3600 seconds
        |      speed = OSM maxspeed x 0.5 (peak hour congestion multiplier)
        |--> Runs Dijkstra's algorithm from each demand zone
        |      cutoff = 600 seconds (10 minutes peak-hour driving)
        |--> Result: reachability_map {zone_i: [reachable station indices]}
        |
        v
set_cover_optimizer.py
        |
        |--> Builds MCLP integer program using Pyomo
        |--> Solves with GLPK solver
        |--> Returns: coordinates of optimal K stations
        |
        v
app.py (FastAPI, port 8000)
        |
        |--> GET /api/spatial-data  → returns all map data to browser
        |--> GET /api/optimize?k=N  → runs solver, returns optimal stations
        |
        v
React Frontend (Vite, port 5173)
        |
        |--> Leaflet map: shows hexagons + candidates + selected stations
        |--> User adjusts K slider → new optimization runs → map updates
```

---

## THE AI/ML FEATURES

### 1. Demand Forecast (Neural Network) — REAL TRAINED MODEL

- **Architecture:** 5 inputs → 8 neurons → 6 neurons → 1 output
- **Trained on:** 8,784 hours of real Mumbai temperature data (Open-Meteo API, 2024)
- **What it predicts:** Electricity demand in MW given hour of day, day of week,
  temperature, traffic index, EV count
- **How we trained it:** scikit-learn MLPRegressor on Python 3.14 (TensorFlow
  doesn't support Python 3.14 yet), then exported weights as JSON for the browser
- **Accuracy:** Mean Absolute Error = 21.1 MW on validation set (well under 30 MW target)
- **The browser runs the model:** JavaScript reads the trained weight matrices and
  performs the forward pass (matrix multiply + ReLU) — no server needed

**What "trained" means here:**
The model learned that demand peaks around 6pm, is higher on weekdays, rises
with temperature (AC load), and correlates with traffic. These are real patterns
learned from real data — not hardcoded rules.

---

### 2. Neural Placement Engine (Station Map) — DEMONSTRATION

- Shows a visual demonstration of neural scoring for each candidate site
- Inputs: EV density, grid capacity, traffic flow, existing coverage, population density
- Each site gets a score from 0–100 showing suitability
- **Note:** The input features are simulated (no per-site real data available)
  but the neural network architecture and forward pass are genuine TF.js

---

### 3. V2C Reinforcement Learning Agent — REAL Q-LEARNING

**V2C = Vehicle-to-Grid:** EVs can push electricity back into the grid during peak demand.

- **Algorithm:** Q-Learning (tabular RL)
- **States:** Low Stress, Medium Stress, High Stress
- **Actions:** Activate V2C, Hold, Deactivate V2C
- **Rewards:** +10 if stress reduced, +2 if held stable, -5 if stress increased
- **Learning rule (Bellman equation):**
  ```
  Q[state][action] = Q[state][action]
    + 0.1 x (reward + 0.9 x max(Q[next_state]) - Q[state][action])
  ```
- The agent starts with random values and learns which action is best in each state
- Over time, cumulative reward trends upward = the agent is genuinely learning

---

## WHAT IS REAL vs SIMULATED

| Component | Real or Simulated | Source |
|---|---|---|
| Mumbai road network | REAL | OpenStreetMap via OSMnx |
| Substation locations | REAL | OpenStreetMap power data |
| Demand zone hexagons | REAL | Uber H3 spatial indexing |
| POI weights | REAL | OpenStreetMap POI data |
| Travel time calculation | REAL | Dijkstra on OSM road graph |
| MCLP optimization | REAL | GLPK mathematical solver |
| Demand model training data | REAL | Open-Meteo 2024 Mumbai temperatures |
| Demand model | REAL TRAINED | scikit-learn MLPRegressor |
| Station placement scores | SIMULATED | No per-site real data available |
| V2C grid stress | SIMULATED | No live grid feed connected |
| RL agent algorithm | REAL | Genuine Q-Learning implementation |

---

## HOW TO DEMO IT (STEP BY STEP)

1. **Open** `http://localhost:5173/`
   - "This is our landing page. VoltGrid is an EV station optimizer for Mumbai."

2. **Click "Launch Dashboard"** → shows `/dashboard`
   - "This overview shows system-wide metrics: total stations, EVs covered, grid stress saved."

3. **Click "Station Map"**
   - "This is the core feature. On the left you see 50 real potential charging site locations.
     The hexagonal heatmap shows demand — brighter = more shops, malls, transit nearby."
   - Move the K slider to 5: "With a budget of only 5 stations, the algorithm picks these 5
     specific locations to cover the maximum weighted demand."
   - Move to 15: "At K=15, we achieve near 100% coverage."
   - Click "Optimize All Stations": "The neural engine scores each site 0–100."

4. **Click "Demand Forecast"**
   - "This neural network was trained on 8,784 hours of real Mumbai temperature data from 2024.
     It predicts electricity demand every 4 seconds using current hour, temperature, and traffic.
     The canvas shows the actual forward pass firing through each layer."

5. **Click "V2C Monitor"**
   - "This reinforcement learning agent is learning when to activate vehicle-to-grid charging.
     It tries actions, receives rewards, and updates its Q-table in real time.
     See the learning curve trending upward — the agent is genuinely improving."

---

## TECH STACK SUMMARY (FOR TECHNICAL JUDGES)

| Layer | Technology | Why chosen |
|---|---|---|
| Road network data | OSMnx + OpenStreetMap | Free, real, global coverage |
| Spatial indexing | Uber H3 | Equal-area hexagons, no edge distortion |
| Graph algorithm | NetworkX Dijkstra | Real shortest-path on road network |
| Optimization | Pyomo + GLPK | Industry-grade ILP solver, open source |
| Backend API | FastAPI (Python) | Fast async REST, auto Swagger docs |
| Frontend | React 18 + Vite | Component-based, hot reload |
| Map rendering | React-Leaflet | Production-grade map library |
| ML training | scikit-learn MLPRegressor | Works on Python 3.14, no TF needed |
| Browser inference | Pure JS matrix math | No TF.js runtime overhead |
| RL agent | Vanilla JavaScript | No library needed for tabular Q-learning |
| Styling | Custom CSS | Dark premium theme, glassmorphism |

---

## POTENTIAL QUESTIONS AND ANSWERS

**Q: Why not just use Google Maps API?**
A: OSMnx gives us the full road network graph programmatically. We need graph
structure (nodes + edges) to run Dijkstra and calculate travel times — not just
routing between two points.

**Q: Why hexagons instead of squares or circles?**
A: Hexagons tile the plane perfectly, have equal area, and each hexagon has equidistant
neighbors — making spatial analysis consistent across the entire city.

**Q: How is this different from just finding the top 10 most popular areas?**
A: The optimizer accounts for coverage overlap. Two stations in the same neighborhood
cover the same people. MCLP forces geographic spread to maximize total unique coverage.

**Q: Why peak-hour 0.5x speed multiplier?**
A: Mumbai has some of the worst traffic in India. A station that's 5 minutes away
in free flow is 10+ minutes during rush hour. We model the realistic worst case
to ensure coverage when people most need it (commute hours).

**Q: Could this scale to all of India?**
A: Yes — the algorithm is city-agnostic. You'd need to download a new .graphml
for any city, and H3 works globally. The MCLP solver scales with number of candidates,
not city size.

---

*VoltGrid — Mumbai EV Charging Station Optimizer*
*Built for HackX 2.0*
