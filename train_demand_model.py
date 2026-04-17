"""
train_demand_model.py

Trains a neural network on synthetic Mumbai demand data using scikit-learn.
Exports weights as JSON so they can be loaded into the TF.js model in the browser.

Works on Python 3.14 — no TensorFlow Python required!

Run:
    python train_demand_model.py
"""

import json
import math
import os
import numpy as np
import requests
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# ─── Step 1: Fetch real Mumbai weather from Open-Meteo (free, no API key) ──
print("Fetching Mumbai weather data from Open-Meteo...")
try:
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=19.07&longitude=72.87"
        "&start_date=2024-01-01&end_date=2024-12-31"
        "&hourly=temperature_2m"
        "&timezone=Asia/Kolkata"
    )
    resp = requests.get(url, timeout=15)
    data = resp.json()
    temps = data["hourly"]["temperature_2m"]
    times = data["hourly"]["time"]
    print(f"  -> {len(temps)} hourly weather records downloaded.")
    df = pd.DataFrame({"datetime": pd.to_datetime(times), "temp": temps})
except Exception as e:
    print(f"  -> Weather fetch failed ({e}), using synthetic temperature.")
    hours = pd.date_range("2024-01-01", periods=8760, freq="h")
    # Mumbai temp: ~24°C winter, ~33°C summer
    temps_synth = 28 + 5 * np.sin(2 * np.pi * (hours.dayofyear - 90) / 365) \
                     + 3 * np.sin(2 * np.pi * hours.hour / 24 - 1)
    df = pd.DataFrame({"datetime": hours, "temp": temps_synth})

df["hour"] = df["datetime"].dt.hour
df["day"]  = df["datetime"].dt.dayofweek   # 0=Monday … 6=Sunday

# ─── Step 2: Simulate traffic and EV count ──────────────────────────────────
# Traffic peaks at 8-10am and 5-8pm on weekdays
def traffic_index(hour, day):
    if day >= 5:  # weekend
        return 0.3 + 0.3 * math.sin(math.pi * hour / 12)
    morning = math.exp(-0.5 * ((hour - 9) / 1.5) ** 2)
    evening = math.exp(-0.5 * ((hour - 18) / 1.5) ** 2)
    return min(1.0, 0.3 + 0.7 * (morning + evening * 0.9))

np.random.seed(42)
df["traffic"]  = df.apply(lambda r: traffic_index(r["hour"], r["day"]), axis=1) \
                 + np.random.normal(0, 0.05, len(df))
df["traffic"]  = df["traffic"].clip(0, 1)
df["ev_count"] = 800 + 400 * df["traffic"] + np.random.normal(0, 50, len(df))

# ─── Step 3: Generate synthetic demand labels ────────────────────────────────
def demand_mw(hour, day, temp, traffic):
    # Time-of-day curve: low at 3am, peaks at 6pm
    time_f   = 0.5 + 0.5 * math.sin(math.pi * (hour - 3) / 15)
    time_f   = max(0, time_f)
    # Weekday boost
    day_f    = 1.15 if day < 5 else 0.85
    # AC load: extra 2% per degree above 28°C
    temp_f   = 1.0 + 0.02 * max(0, temp - 28)
    # Traffic boosts demand slightly
    traf_f   = 1.0 + 0.1 * traffic
    return 300 + 380 * time_f * day_f * temp_f * traf_f

df["actual_mw"] = df.apply(
    lambda r: demand_mw(r["hour"], r["day"], r["temp"], r["traffic"]),
    axis=1
) + np.random.normal(0, 15, len(df))   # add realistic noise

df = df.dropna()
print(f"\nDataset: {len(df)} samples")
print(f"  MW range: {df['actual_mw'].min():.0f} – {df['actual_mw'].max():.0f} MW")
print(f"  Temp range: {df['temp'].min():.1f} – {df['temp'].max():.1f} °C")

# ─── Step 4: Prepare features and normalize ──────────────────────────────────
FEATURES = ["hour", "day", "temp", "traffic", "ev_count"]
X = df[FEATURES].values
y = df["actual_mw"].values

scaler_X = MinMaxScaler()
scaler_y = MinMaxScaler()

X_scaled = scaler_X.fit_transform(X)
y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

X_train, X_val, y_train, y_val = train_test_split(
    X_scaled, y_scaled, test_size=0.15, random_state=42
)

# ─── Step 5: Train the neural network ────────────────────────────────────────
print("\nTraining neural network (8 hidden, 6 hidden)...")
mlp = MLPRegressor(
    hidden_layer_sizes=(8, 6),
    activation="relu",
    solver="adam",
    learning_rate_init=0.001,
    max_iter=500,
    random_state=42,
    verbose=False,
    early_stopping=True,
    validation_fraction=0.1,
    n_iter_no_change=20
)
mlp.fit(X_train, y_train)

# ─── Step 6: Evaluate ────────────────────────────────────────────────────────
y_pred_scaled = mlp.predict(X_val)
y_pred_mw = scaler_y.inverse_transform(y_pred_scaled.reshape(-1, 1)).ravel()
y_true_mw = scaler_y.inverse_transform(y_val.reshape(-1, 1)).ravel()

mae = mean_absolute_error(y_true_mw, y_pred_mw)
print(f"  Validation MAE: {mae:.1f} MW  (target < 30 MW)")
print(f"  Iterations: {mlp.n_iter_}")

# ─── Step 7: Export weights as JSON for TF.js ────────────────────────────────
# scikit-learn MLP weight format:
#   coefs_[0]  shape (n_features, hidden1)    → Dense layer 1 kernel
#   intercepts_[0]  shape (hidden1,)          → Dense layer 1 bias
#   coefs_[1]  shape (hidden1, hidden2)       → Dense layer 2 kernel
#   intercepts_[1]  shape (hidden2,)          → Dense layer 2 bias
#   coefs_[2]  shape (hidden2, 1)             → Output layer kernel
#   intercepts_[2]  shape (1,)                → Output layer bias

out_dir = os.path.join("frontend", "public", "demand_model")
os.makedirs(out_dir, exist_ok=True)

weights = {
    "layer1": {
        "kernel": mlp.coefs_[0].tolist(),      # shape (5, 8)
        "bias":   mlp.intercepts_[0].tolist()  # shape (8,)
    },
    "layer2": {
        "kernel": mlp.coefs_[1].tolist(),      # shape (8, 6)
        "bias":   mlp.intercepts_[1].tolist()  # shape (6,)
    },
    "output": {
        "kernel": mlp.coefs_[2].tolist(),      # shape (6, 1)
        "bias":   mlp.intercepts_[2].tolist()  # shape (1,)
    }
}

scaler_data = {
    "X_min":   scaler_X.data_min_.tolist(),
    "X_range": scaler_X.data_range_.tolist(),
    "y_min":   float(scaler_y.data_min_[0]),
    "y_range": float(scaler_y.data_range_[0])
}

with open(os.path.join(out_dir, "weights.json"), "w") as f:
    json.dump(weights, f)
with open(os.path.join(out_dir, "scaler.json"), "w") as f:
    json.dump(scaler_data, f)

print(f"[OK] Weights saved to {out_dir}/weights.json")
print(f"[OK] Scaler saved to  {out_dir}/scaler.json")
print("\nNext step: The React app will automatically use these weights.")
print("Refresh http://localhost:5173/demand in your browser!")
