# How to Train TensorFlow on Real Data — VoltGrid

> Current status: The TF.js models in the app use **random weights** and produce meaningless outputs.
> This document explains how to fix that with real training data.

---

## The Problem with the Current Models

```javascript
// What's happening right now in DemandForecast.jsx:
const model = tf.sequential();
model.add(tf.layers.dense({ inputShape: [5], units: 8, activation: "relu" }));
model.add(tf.layers.dense({ units: 6, activation: "relu" }));
model.add(tf.layers.dense({ units: 1, activation: "linear" }));
// ← weights are RANDOM, model is NEVER trained
// Output × 800 = just noise scaled to look like MW values
```

The model produces numbers that look like MW predictions but have
**zero relationship** to actual electricity demand.

---

## Option A — Train in Python, Deploy to Browser (RECOMMENDED)

This is the production-grade approach used in industry.

### Step 1: Install required Python packages

```bash
pip install tensorflow tensorflowjs scikit-learn pandas requests
```

### Step 2: Collect real training data

For demand prediction you need historical data:

| Feature (Input X) | Where to get it |
|---|---|
| Hour of day (0–23) | Generate from timestamps |
| Day of week (0–6) | Generate from timestamps |
| Temperature °C | Open-Meteo API (free, no key needed) |
| Traffic index (0–1) | TomTom / Google Maps API |
| EV count in area | MSEDCL / Maharashtra EV data / Vahan |
| **Output label (y)** | **Actual grid load in MW (POSOCO/NLDC)** |

### Step 3: Fetch free weather data (Open-Meteo, no API key needed)

```python
import requests
import pandas as pd

# Free historical weather for Mumbai — no API key required
url = (
    "https://archive-api.open-meteo.com/v1/archive"
    "?latitude=19.07&longitude=72.87"
    "&start_date=2024-01-01&end_date=2024-12-31"
    "&hourly=temperature_2m"
    "&timezone=Asia/Kolkata"
)
resp = requests.get(url).json()
temps = resp["hourly"]["temperature_2m"]
times = resp["hourly"]["time"]

df = pd.DataFrame({"datetime": pd.to_datetime(times), "temp": temps})
df["hour"] = df["datetime"].dt.hour
df["day"]  = df["datetime"].dt.dayofweek
```

### Step 4: Generate synthetic demand labels (if you don't have MSEDCL data)

```python
import numpy as np

# Realistic demand formula for Mumbai:
# - Peaks at 6pm (hour 18), lowest at 3am (hour 3)
# - Higher on weekdays, higher in summer
def synthetic_demand(hour, day, temp):
    # Time-of-day curve (sine wave peaking at 6pm)
    time_factor = 0.5 + 0.5 * np.sin(np.pi * (hour - 3) / 15)
    # Weekday boost
    weekday_factor = 1.15 if day < 5 else 0.85
    # Temperature effect (AC load in summer)
    temp_factor = 1.0 + 0.02 * max(0, temp - 28)
    # Base demand 300 MW, peak ~700 MW
    return 300 + 400 * time_factor * weekday_factor * temp_factor

df["traffic"] = 0.3 + 0.5 * np.sin(np.pi * df["hour"] / 12).clip(0)
df["ev_count"] = 800 + 400 * np.random.rand(len(df))
df["actual_mw"] = df.apply(
    lambda r: synthetic_demand(r["hour"], r["day"], r["temp"]) + np.random.randn() * 20,
    axis=1
)

df.to_csv("mumbai_demand.csv", index=False)
print(f"Generated {len(df)} training samples")
```

### Step 5: Train the model

```python
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split

df = pd.read_csv("mumbai_demand.csv").dropna()

X = df[["hour", "day", "temp", "traffic", "ev_count"]].values
y = df["actual_mw"].values / 800  # normalize to 0–1 for training

# Normalize inputs
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_val, y_train, y_val = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Same architecture as the browser model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(8,  activation="relu", input_shape=(5,)),
    tf.keras.layers.Dense(6,  activation="relu"),
    tf.keras.layers.Dense(1,  activation="linear")
])

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss="mse",
    metrics=["mae"]
)

history = model.fit(
    X_train, y_train,
    epochs=100,
    batch_size=32,
    validation_data=(X_val, y_val),
    verbose=1
)

# Check accuracy
val_mae = min(history.history["val_mae"])
print(f"Validation MAE: {val_mae * 800:.1f} MW")  # should be < 30 MW

# Save scaler parameters (needed in browser)
import json
scaler_params = {
    "min": scaler.data_min_.tolist(),
    "scale": scaler.data_range_.tolist()
}
with open("frontend/public/demand_model/scaler.json", "w") as f:
    json.dump(scaler_params, f)
```

### Step 6: Export model to TF.js format

```bash
pip install tensorflowjs
```

```python
import tensorflowjs as tfjs

# Save in TF.js format — creates model.json + weight files
tfjs.converters.save_keras_model(model, "frontend/public/demand_model")
print("Model saved! Files created in frontend/public/demand_model/")
```

### Step 7: Load trained model in React (DemandForecast.jsx)

Replace the `buildDemandModel()` function with this:

```javascript
// Load trained model from public folder
let trainedModel = null;
let scalerParams = null;

async function loadTrainedModel() {
  if (trainedModel) return trainedModel;

  // Load scaler parameters
  const scalerResp = await fetch("/demand_model/scaler.json");
  scalerParams = await scalerResp.json();

  // Load trained TF.js model
  trainedModel = await window.tf.loadLayersModel("/demand_model/model.json");
  console.log("Trained model loaded!");
  return trainedModel;
}

function normalizeInput(hour, day, temp, traffic, evCount) {
  // Apply the same MinMaxScaler used in Python
  const raw = [hour, day, temp, traffic, evCount];
  return raw.map((v, i) =>
    (v - scalerParams.min[i]) / scalerParams.scale[i]
  );
}

// In your forward pass:
const model = await loadTrainedModel();
const normalized = normalizeInput(hour, day, temp, traffic, evCount);
const tensor = window.tf.tensor2d([normalized]);
const pred   = model.predict(tensor);
const mw     = (await pred.data())[0] * 800;  // de-normalize
```

---

## Option B — Online Learning (Train as new data arrives)

If you can get a real-time data feed, train the model live in the browser:

```javascript
// First, compile the model (currently missing in the code)
model.compile({
  optimizer: tf.train.adam(0.001),
  loss: "meanSquaredError"
});

// Every time you receive real grid load data:
const realMW = await fetchCurrentGridLoad();  // your real data source

// Train on this single new observation
const loss = await model.fit(
  tf.tensor2d([[hour/24, day/7, temp, traffic, ev]]),
  tf.tensor2d([[realMW / 800]]),  // normalize to 0–1
  { epochs: 3, verbose: 0 }
);
console.log("Updated model, loss:", loss.history.loss[0]);
```

This is **online learning** — the model improves with every new data point automatically.

---

## Option C — Use Pre-trained LSTM for Time Series (Advanced)

For electricity demand (which is a time series), an **LSTM** is more accurate than a Dense network:

```python
# Python training — LSTM takes sequences as input
model = tf.keras.Sequential([
    tf.keras.layers.LSTM(32, input_shape=(24, 5)),  # 24 hours of history
    tf.keras.layers.Dense(16, activation="relu"),
    tf.keras.layers.Dense(1)
])
```

This lets the model learn *patterns across time* (e.g., Monday morning always spikes after 8am).

---

## Free Real Data Sources

| Data | URL | Notes |
|---|---|---|
| Mumbai weather (historical + live) | https://open-meteo.com | Free, no API key |
| India real-time grid load | https://www.nldc.in/ | POSOCO real-time data |
| India grid data API | https://api.energy.rajasthan.gov.in | Some state APIs are public |
| EV registrations by state | https://vahan.parivahan.gov.in/vahan4dashboard | Government data |
| Traffic (India) | https://developer.tomtom.com | Free tier: 2500 calls/day |

---

## Quickest Path to a Real Working Model

If you want something working this weekend:

1. Run the `synthetic_demand` script above (5 minutes, generates 8,760 samples)
2. Train the Keras model (2 minutes on CPU)
3. Export with `tensorflowjs`
4. Update `DemandForecast.jsx` to load from `/demand_model/model.json`

Your model won't be perfect, but it will be **genuinely trained** with
realistic patterns (daily peaks, temperature effect, weekday vs weekend)
— far better than random weights.

---

## Summary: What Changes in the Code

| File | Change |
|---|---|
| `train_demand_model.py` | **NEW** — Python training script (run once offline) |
| `frontend/public/demand_model/` | **NEW** — Exported TF.js model files |
| `frontend/public/demand_model/scaler.json` | **NEW** — Normalization parameters |
| `frontend/src/pages/DemandForecast.jsx` | Replace `buildDemandModel()` with `loadTrainedModel()` |

---

*VoltGrid — Mumbai EV Charging Station Optimizer*
