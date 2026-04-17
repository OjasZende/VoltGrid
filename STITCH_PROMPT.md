# VoltGrid — Google Stitch UI Prompt

Copy everything below this line and paste it into Google Stitch:

---

## PROMPT FOR STITCH

Design a premium, dark-themed web application called **VoltGrid** — an AI-powered EV (Electric Vehicle) charging station optimizer for Mumbai, India.

---

### BRAND & DESIGN STYLE

- **App name:** VoltGrid
- **Logo:** Lightning bolt icon ⚡ in cyan next to "VoltGrid" in bold white
- **Theme:** Ultra-dark, premium, futuristic — similar to a Bloomberg Terminal or Palantir dashboard
- **Primary background:** Deep navy `#0a0f1e`
- **Panel background:** Dark slate `#0f172a` with subtle borders `#1e293b`
- **Accent color:** Electric cyan `#06b6d4`
- **Secondary accent:** Purple `#8b5cf6`
- **Success color:** Neon green `#10b981`
- **Warning color:** Amber `#f59e0b`
- **Danger color:** Red `#ef4444`
- **Text primary:** White `#f8fafc`
- **Text muted:** Slate `#94a3b8`
- **Font:** Inter (Google Fonts) — clean, modern, technical
- **Style elements:**
  - Glassmorphism cards with `backdrop-filter: blur`
  - Subtle gradient borders that glow on hover
  - Neon glow effects on active elements (`box-shadow: 0 0 20px cyan`)
  - Smooth transitions on all interactive elements
  - Dark grid background pattern (subtle dots or lines)
  - Animated status indicators (pulsing green dots)

---

### NAVIGATION (Top Navbar)

Sticky top navbar, 64px tall, dark background with subtle border-bottom.

Left side:
- Lightning bolt emoji ⚡ + "VoltGrid" in bold white (18px)
- Subtitle: "Mumbai EV Optimizer" in muted cyan (11px)

Center/Right navigation links (horizontal, pill-style active state):
1. **Dashboard** — grid icon
2. **Station Map** — map pin icon
3. **Demand Forecast** — chart line icon
4. **V2C Monitor** — battery icon

Far right:
- Current time display (live clock): `18:03:49`
- Red pulsing badge: `● LIVE`

---

### PAGE 1 — DASHBOARD (`/dashboard`)

Layout: Full-width dark page with 32px padding.

**Top row — 4 stat cards (equal width grid):**

Each card has:
- Small label in muted uppercase text
- Large bold number in accent color
- Small delta line (e.g. "↑ 12 this month" in green)
- Subtle icon top-right (faded)

Cards:
1. **TOTAL STATIONS** | `500` (cyan) | ↑ 12 this month
2. **EVS COVERED** | `10,00,000` (purple) | ↑ 8.2% YoY
3. **GRID STRESS SAVED** | `34%` (green) | ↑ 3% vs last week
4. **ACTIVE V2C NODES** | `1,240` (amber) | ↓ 42 offline

**Middle row — 2 charts side by side:**

Left chart (wider, ~65% width):
- Title: "TODAY'S DEMAND CURVE" in muted uppercase
- Smooth cyan line chart over dark grid
- X-axis: hours 0:00 to 23:00
- Y-axis: 0 to 700
- Area fill gradient under the line (cyan → transparent)
- The line should have a realistic wave shape: low at 3am (~100), rising at 6am, peak at 6pm (~620), declining at 11pm (~200)

Right chart (~35% width):
- Title: "STATION STATUS MIX"
- Donut chart with 4 segments:
  - Available 58% (green)
  - Busy 27% (amber)
  - Overcrowded 8% (red)
  - Offline 7% (grey)
- Legend with colored dots below
- Thick donut ring, dark hole in center

**Bottom strip:**
- "System: ● LIVE" and "Uptime: 99.8%" in small cards

---

### PAGE 2 — STATION MAP (`/map`)

Layout: Full-height split layout.

**Left sidebar (280px wide, dark, scrollable):**

Section: "Mumbai EV Station Optimizer"
- Slider control: "Station Budget (K)" — 1 to 30, shows value
- Checkboxes: "Show Demand Grid", "Color by POI weight"
- Legend: Red dot = Unoptimized, Green bolt = Selected, Grey = Candidate
- 4 metric cards in 2×2 grid:
  - H3 Demand Points: 376
  - Candidate Sites: 50
  - POI Weight Covered: 100.0% (large green number)
  - Budget Used: 7/10
- Divider
- Section: "🧠 NEURAL PLACEMENT ENGINE" (purple header)
- Large gradient button: "⚡ Optimize All Stations" (cyan→purple gradient)
- After clicking: bar chart showing "TOP 5 BY NEURAL SCORE"
  - Site #1: bar at 87% (cyan fill)
  - Site #30: bar at 84%
  - Site #33: bar at 81%
  - Site #34: bar at 79%
  - Site #7: bar at 74%

**Main area:**
- Dark map (CartoDB dark tiles) filling remaining space
- Two tabs above map: "🔴 Before (All Sites)" | "🟢 After (Optimized)"
- Green glowing bolt markers for selected stations
- Semi-transparent green circles showing coverage radius
- Hexagonal heatmap overlay (yellow-orange for high demand, dark for low)

---

### PAGE 3 — DEMAND FORECAST (`/demand`)

Layout: Full-width, padded.

**Section 1: Neural Prediction Engine card**

Header row:
- Title: "🧠 Neural Prediction Engine"
- Badge: "✅ Trained Model" (green border)

Two columns inside the card:

Left column (canvas neural network diagram):
- Dark background with subtle grid lines
- 4 vertical columns of nodes connected by lines:
  - Column 1 (cyan): 5 nodes labeled: Hour, Day, Temp, Traffic, EV Count
  - Column 2 (purple): 8 nodes (no labels, smaller)
  - Column 3 (purple): 6 nodes
  - Column 4 (green): 1 node labeled "MW Demand"
- Connections between all nodes as thin grey lines
- When "firing": connections glow cyan, nodes light up left-to-right
- Layer labels below each column: Input, Hidden 1, Hidden 2, Output

Right column (live prediction panel):
- "LIVE INPUTS" heading (muted uppercase)
- 5 rows each showing label + value:
  - Hour: 14:00 (cyan value)
  - Day: Wed
  - Temp: 31.4 °C
  - Traffic: 72%
  - EV Count: 1,240
- Divider line
- "OUTPUT PREDICTION" heading
- Large display: "487 MW" (giant cyan, glowing)
- Confidence bar: label + colored fill bar + "91.4%"

**Section 2: Demand curve chart**
- Title: "TODAY'S DEMAND CURVE (NEURAL ESTIMATES)"
- Cyan sparkline over dark background, showing 20 recent predictions
- Area fill below the line

---

### PAGE 4 — V2C MONITOR (`/v2c`)

Layout: Full-width, padded.

Header: "🔋 V2C Monitor" + LIVE badge + "Episode 42" purple pill

**Grid of 4 cards (2×2):**

Card 1 — Agent Status:
- Grid Stress: amber pill "Medium Stress"
- Last Action: cyan pill "Activate V2C"
- Cumulative Reward: large "+124" in green
- Episode: "42"

Card 2 — Agent Learning Curve:
- Title: "Agent Learning Curve"
- SVG line chart trending upward (reward increasing over time)
- Cyan line, gradient area fill, dot at latest point
- Labels: "Reward: 0" and "Latest: +124"

Card 3 — Q-Table (full width, spans both columns):
- Title: "Q-Table"
- 3×4 dark table:
  - Rows: Low Stress | Medium Stress | High Stress
  - Columns: State\Action | Activate V2C | Hold | Deactivate V2C
  - Values: floating point numbers like 1.24, 0.87, -0.43
  - One cell highlighted with cyan glow (the currently chosen action)

Card 4 — Decision Log (full width):
- Title: "Decision Log"
- List of 5–6 recent decisions, each row:
  - Timestamp (muted) | State (amber) | → | Action (cyan) | +10 (green) or -5 (red)
  - Left border: 3px cyan line
  - Dark background per row

---

### LANDING PAGE (`/`)

Full-screen hero, no navbar on this page.

**Hero section:**
- Dark background with animated particle grid or subtle moving gradient
- Center content:
  - Small badge: "🚗 Mumbai EV Infrastructure" (cyan pill)
  - H1: "Power the Future of" (white, large)
  - H1 continued: "EV Mobility" (cyan gradient text, larger)
  - Paragraph: "AI-driven optimization for EV charging station placement across Mumbai using real road network data, mathematical optimization, and live neural predictions."
  - Two CTA buttons side by side:
    - "Launch Dashboard →" (filled cyan gradient, large, rounded)
    - "View Station Map" (outlined, white border)

**Below hero — 3 feature cards in a row:**

Card 1: "⚡ MCLP Optimization"
- "Mathematical optimization using Pyomo + GLPK solver to find the provably optimal placement of charging stations across Mumbai's real road network."

Card 2: "🧠 Neural Demand Prediction"
- "Trained neural network on 8,784 hours of real Mumbai temperature data. Predicts electricity demand with 21 MW accuracy."

Card 3: "🤖 Reinforcement Learning"
- "Q-Learning agent that learns when to activate Vehicle-to-Grid charging to reduce grid stress and maximize reward."

---

### COMPONENT SPECIFICATIONS

**Buttons:**
- Primary: `background: linear-gradient(135deg, #06b6d4, #8b5cf6)`, white text, 10px radius, 12px 24px padding
- On hover: translateY(-2px), brighter shadow

**Cards:**
- Background: `#0f172a`
- Border: `1px solid #1e293b`
- Border-radius: 12–16px
- Padding: 20–24px
- On hover (stat cards): translateY(-2px)

**Pill badges:**
- Rounded 99px
- Colored background at 15–20% opacity
- Matching colored border and text

**Charts:**
- Background: `#0a1628` (slightly darker than cards)
- Grid lines: `rgba(148, 163, 184, 0.08)` dashed
- All chart text: muted grey

**Tables:**
- Dark header row `#0f172a`
- Cell borders: `1px solid #1e293b`
- Active/highlighted cell: cyan background at 25% opacity, cyan text, inner glow

---

### ANIMATIONS & INTERACTIONS

- All cards: smooth `transform` on hover with 200ms transition
- Navbar active link: pill background highlight with subtle glow
- Live badge: opacity pulse animation (1 → 0.5 → 1) every 2 seconds
- Neural diagram: nodes light up sequentially left to right every 4 seconds
- Q-table active cell: glowing cyan highlight updates every 5 seconds
- Chart lines: smooth SVG path transitions when data updates
- Stat card values: subtle number roll animation when page loads
- Toast notification: slides up from bottom-right, fades out after 4 seconds

---

### RESPONSIVE BEHAVIOR

- Desktop (>1200px): full layouts as described above
- Tablet (768–1200px): stat cards 2×2, charts stack vertically
- Mobile (<768px): single column, sidebar becomes bottom sheet on Station Map

---

### TECH STACK CONTEXT (so Stitch understands the data flow)

- Frontend: React 18 + Vite
- Routing: React Router v6
- Map: React-Leaflet
- CSS: Pure CSS (no Tailwind)
- Backend API: FastAPI at `http://localhost:8000`
  - `GET /api/spatial-data` → returns map data
  - `GET /api/optimize?k=N` → returns optimal station coordinates
- Neural model: weights loaded from `/demand_model/weights.json`
- All icons: emoji or Lucide React icons

---

END OF PROMPT
