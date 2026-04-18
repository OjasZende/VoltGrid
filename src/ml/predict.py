import pickle
import pandas as pd
import numpy as np
import os

_demand_model = None
_queue_model = None

def _get_st_cache():
    try:
        import streamlit as st
        return st.cache_resource
    except ImportError:
        return lambda x: x

@_get_st_cache()
def _load_model(model_path):
    if not os.path.exists(model_path):
        return None  # Return None instead of raising Error for fallback safety
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def predict_demand(df: pd.DataFrame):
    global _demand_model
    if _demand_model is None:
        _demand_model = _load_model('models/demand_xgb.pkl')
    if _demand_model is None:
        raise FileNotFoundError("Demand model file missing.")
    return _demand_model.predict(df)

def predict_queue(df: pd.DataFrame):
    global _queue_model
    if _queue_model is None:
        _queue_model = _load_model('models/queue_xgb.pkl')
    if _queue_model is None:
        raise FileNotFoundError("Queue model file missing.")
    return _queue_model.predict(df)
