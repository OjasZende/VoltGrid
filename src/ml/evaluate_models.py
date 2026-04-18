import pandas as pd
import numpy as np
import pickle
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

def load_data_and_model(data_path, model_path, target_col):
    df = pd.read_csv(data_path)
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
        
    print(f"\n--- Data Inspection: {target_col} ---")
    print(f"Min: {df[target_col].min():.2f}")
    print(f"Max: {df[target_col].max():.2f}")
    print(f"Mean: {df[target_col].mean():.2f}")
    
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    y_pred = model.predict(X_test)
    
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    
    print(f"\n--- Evaluation: {target_col} ---")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R²: {r2:.2f}")
    
    print(f"\n--- Sample Predictions: {target_col} ---")
    sample_actual = y_test.head(10).values
    sample_pred = y_pred[:10]
    for actual, pred in zip(sample_actual, sample_pred):
        print(f"Actual: {actual:.2f} | Predicted: {pred:.2f}")
        
    return mae, rmse, r2

if __name__ == "__main__":
    print("DEMAND MODEL:")
    load_data_and_model('data/processed/demand_training.csv', 'models/demand_xgb.pkl', 'demand_score')
    
    print("\n" + "="*50 + "\n")
    
    print("QUEUE MODEL:")
    load_data_and_model('data/processed/queue_training.csv', 'models/queue_xgb.pkl', 'queue_minutes')
