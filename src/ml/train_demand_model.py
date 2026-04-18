import os
import pandas as pd
import pickle
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

def train():
    df = pd.read_csv('data/processed/demand_training.csv')
    X = df.drop(columns=['demand_score'])
    y = df['demand_score']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = XGBRegressor(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    
    os.makedirs('models', exist_ok=True)
    with open('models/demand_xgb.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    print(f"Demand Model trained successfully!")
    print(f"Mean Absolute Error (MAE): {mae:.2f}")

if __name__ == "__main__":
    train()
