import os
import pandas as pd
import numpy as np

def generate_demand_data(n_samples=1000):
    np.random.seed(42)
    hour = np.random.randint(0, 24, n_samples)
    day_of_week = np.random.randint(0, 7, n_samples)
    traffic_score = np.random.uniform(0, 100, n_samples)
    parking_density = np.random.uniform(0, 1, n_samples)
    grid_capacity = np.random.uniform(50, 500, n_samples) # KW
    existing_station_count = np.random.randint(0, 10, n_samples)
    ev_registrations = np.random.randint(100, 5000, n_samples)
    
    # Simple linear relationship for demand score with some noise
    demand_score = (
        (traffic_score * 0.4) + 
        (parking_density * 50) + 
        (ev_registrations * 0.01) - 
        (existing_station_count * 5)
    )
    # Peak hour boost
    demand_score += np.where((hour >= 8) & (hour <= 18), 20, 0)
    demand_score = np.clip(demand_score, 0, 100) + np.random.normal(0, 5, n_samples)
    
    df = pd.DataFrame({
        'hour': hour,
        'day_of_week': day_of_week,
        'traffic_score': traffic_score,
        'parking_density': parking_density,
        'grid_capacity': grid_capacity,
        'existing_station_count': existing_station_count,
        'ev_registrations': ev_registrations,
        'demand_score': np.clip(demand_score, 0, 100)
    })
    return df

def generate_queue_data(n_samples=1000):
    np.random.seed(42)
    hour = np.random.randint(0, 24, n_samples)
    day_of_week = np.random.randint(0, 7, n_samples)
    nearby_demand_score = np.random.uniform(0, 100, n_samples)
    total_ports = np.random.randint(2, 20, n_samples)
    fast_charger_ports = np.random.randint(0, 10, n_samples)
    historical_sessions = np.random.randint(10, 500, n_samples)
    
    # Calculate queue minutes
    queue_minutes = (
        (nearby_demand_score * 0.5) + 
        (historical_sessions * 0.1) - 
        (total_ports * 2) - 
        (fast_charger_ports * 3)
    )
    # Peak hour effect
    queue_minutes += np.where((hour >= 17) & (hour <= 20), 15, 0)
    queue_minutes = np.clip(queue_minutes, 0, 120) + np.random.normal(0, 5, n_samples)
    
    df = pd.DataFrame({
        'hour': hour,
        'day_of_week': day_of_week,
        'nearby_demand_score': nearby_demand_score,
        'total_ports': total_ports,
        'fast_charger_ports': fast_charger_ports,
        'historical_sessions': historical_sessions,
        'queue_minutes': np.clip(queue_minutes, 0, 120)
    })
    return df

if __name__ == "__main__":
    os.makedirs('data/processed', exist_ok=True)
    
    print("Generating synthetic demand data...")
    demand_df = generate_demand_data()
    demand_df.to_csv('data/processed/demand_training.csv', index=False)
    
    print("Generating synthetic queue data...")
    queue_df = generate_queue_data()
    queue_df.to_csv('data/processed/queue_training.csv', index=False)
    
    print("Data generation complete!")
