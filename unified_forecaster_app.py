import os
import json
import logging
import re
import pickle
import joblib 
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd
import numpy as np
import uvicorn

# --- External Libraries ---
from fastapi import FastAPI
from pydantic import BaseModel, Field
import tensorflow as tf
from prophet import Prophet 
import lightgbm as lgb

#unified_forecaster_app.py

# Try importing XGBoost DMatrix (optional, for some XGBoost versions)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# NOTE: LightGBM/LSTM dependencies are handled by joblib/tf.keras.models


# --------------------------------------------------------------
# 0. SHARED PYDANTIC MODEL
# --------------------------------------------------------------
class ColumnMapping(BaseModel):
    """Maps user columns to model inputs."""
    date_col: str = Field(..., example="WorkDate")
    target_col: str = Field(..., example="NumberOfPieces")
    regressor_cols: Optional[List[str]] = Field(
        None, example=["Customer", "Location"]
    )

# --------------------------------------------------------------
# 1. CORE FORECASTING LOGIC & MODEL CONFIG
# --------------------------------------------------------------

# --- Directory Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models")
KB_MODELS_DIR = os.path.join(BASE_DIR, "knowledge_base", "models")


# --- Model Paths and Metadata Registry ---
MODEL_CONFIGS = {
    'prophet_weekly_v1': {
        'model_path': os.path.join(MODEL_DIR, "prophet_weekly_v1.pkl"),
        'metadata_path': os.path.join(KB_MODELS_DIR, "prophet_weekly.json"), # Renamed to match uploaded file
        'freq': 'W',
    },
    'lightgbm_model': { 
        'model_path': os.path.join(MODEL_DIR, "lightgbm_model.pkl"),
        'metadata_path': os.path.join(KB_MODELS_DIR, "lightgbm_model_metadata.json"),
        'freq': 'ME',  # Monthly end frequency (replaces deprecated 'M')
        'lags_steps': [], # No lags used in this minimal training
        'rolling_windows': [], # No rollings used
    },
    'xgboost_v1': {
        'model_path': os.path.join(MODEL_DIR, "xgboost_model.joblib"),
        'metadata_path': os.path.join(KB_MODELS_DIR, "xgboost_v1.json"),
        'freq': 'ME',  # Monthly end frequency (replaces deprecated 'M')
        'lags_steps': [1, 3, 6],
        'rolling_windows': [3, 6, 12],
    },
    'lstm_v1': {
        'model_path': os.path.join(MODEL_DIR, "lstm_v1.h5"),
        'metadata_path': os.path.join(KB_MODELS_DIR, "lstm_v1.json"), 
        'scaler_path': os.path.join(MODEL_DIR, "lstm_preprocessor_v1.pkl"),
        'time_steps': 12, 
        'freq': 'D', 
    },
    'sarima_daily_v1': {
        'model_path': os.path.join(MODEL_DIR, "sarimax_model.pkl"),
        'metadata_path': os.path.join(KB_MODELS_DIR, "sarimax_metadata.json"),
        'freq': 'D',  # Daily frequency
    }
}
# --- Global Dictionaries for Loaded Assets ---
LOADED_MODELS: Dict[str, Any] = {}
LOADED_SCALERS: Dict[str, Any] = {}

# --- Utility Function: Load Model and Metadata ---
def load_model_and_metadata(model_name: str, model_path: str, metadata_path: str):
    """Loads model and metadata based on model type."""
    
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata not found for {model_name}: {metadata_path}")
    with open(metadata_path, 'r') as f:
        try:
            metadata = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"JSON Syntax Error in {metadata_path}: {e.msg}", e.doc, e.pos)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found for {model_name}: {model_path}")
        
    model = None
    
    if model_name == 'lstm_v1': 
        try:
            # Try loading with standard method
            model = tf.keras.models.load_model(model_path, compile=False)
        except Exception as e:
            # Handle compatibility issues with older Keras models (batch_shape parameter)
            error_str = str(e)
            if 'batch_shape' in error_str or 'Unrecognized keyword arguments' in error_str:
                # Try using safe_mode=False or loading with compatibility layer
                try:
                    # Method 1: Try with safe_mode=False (if available in newer TF versions)
                    try:
                        model = tf.keras.models.load_model(model_path, compile=False, safe_mode=False)
                    except TypeError:
                        # safe_mode not available, try alternative method
                        # Method 2: Load model architecture and weights separately
                        import h5py
                        with h5py.File(model_path, 'r') as f:
                            # Try to reconstruct model without the problematic layer config
                            model_config = f.attrs.get('model_config')
                            if model_config:
                                # json is already imported at module level
                                config_dict = json.loads(model_config.decode('utf-8'))
                                # Remove batch_shape from input layer config
                                if 'config' in config_dict and 'layers' in config_dict['config']:
                                    for layer in config_dict['config']['layers']:
                                        if 'config' in layer and 'batch_shape' in layer['config']:
                                            del layer['config']['batch_shape']
                                # Reconstruct model
                                model = tf.keras.models.model_from_json(json.dumps(config_dict), compile=False)
                                # Load weights
                                model.load_weights(model_path)
                        print(f"Warning: LSTM model loaded with compatibility workaround for batch_shape issue")
                except Exception as e2:
                    # If all methods fail, raise a clear error
                    print(f"Warning: Could not load LSTM model due to TensorFlow/Keras version compatibility.")
                    print(f"Error: {error_str}")
                    print("The app will continue without the LSTM model. Other models will work normally.")
                    raise IOError(f"LSTM model compatibility error. The model was saved with an older Keras version. "
                                f"Please retrain the model with the current TensorFlow version, or downgrade TensorFlow to match the model version.")
            else:
                raise
    else:
        try:
            # Compatibility shim for pickled artifacts saved with NumPy 2.x
            # Some artifacts reference the private module 'numpy._core' which
            # does not exist in NumPy 1.x. Map it to 'numpy.core' before unpickling.
            try:
                import sys  # local import to avoid polluting module scope
                import numpy as _np  # alias to avoid shadowing
                if 'numpy._core' not in sys.modules:
                    sys.modules['numpy._core'] = _np.core  # type: ignore[attr-defined]
            except Exception:
                # Best-effort shim; proceed even if aliasing fails
                pass
            if model_path.endswith(('.joblib', '.pkl')):
                model = joblib.load(model_path) if model_path.endswith('.joblib') else pickle.load(open(model_path, 'rb'))
            else:
                 with open(model_path, 'rb') as f:
                    model = pickle.load(f)
        except Exception as e:
            raise IOError(f"Failed to load model {model_name} from {model_path}: {e}")
        
    return model, metadata 

# CODE from unified_forecaster_app.py (Final Corrected prepare_data function)

# CODE from unified_forecaster_app.py (Final Corrected prepare_data function)

def prepare_data(model_id: str, df: pd.DataFrame, mapping: ColumnMapping, metadata: dict, scaler: object = None):
    """Prepares data for model prediction based on model type and config."""
    
    date_col = mapping.date_col
    target_col = mapping.target_col
    
    # CRITICAL FIX 1: Ensure the date column is explicitly converted to datetime FIRST
    # This guarantees the .dt accessor works later in the function.
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce') 

    if model_id == 'prophet_weekly_v1':
        df_prep = df.rename(columns={date_col: 'ds', target_col: 'y'})
        return df_prep[['ds', 'y']]

    elif model_id == 'lstm_v1':
        if scaler is None:
            raise ValueError("LSTM scaler is missing.")
        
        df_prep = df.copy() # Operate on a copy
        # Determine expected feature list from metadata or scaler
        all_lstm_features = metadata.get('required_features', metadata.get('usage_notes', {}).get('required_columns', []))
        if not all_lstm_features:
            scaler_expected = getattr(scaler, 'feature_names_in_', None)
            if scaler_expected is not None and len(scaler_expected) > 0:
                all_lstm_features = list(scaler_expected)
            else:
                raise ValueError("LSTM metadata/scaler missing required feature names.")
             
        # 2. Generate temporal features (THIS IS NOW GUARANTEED TO WORK)
        df_prep['dayofweek'] = df_prep[date_col].dt.dayofweek
        df_prep['month'] = df_prep[date_col].dt.month
        df_prep['year'] = df_prep[date_col].dt.year
        df_prep['quarter'] = df_prep[date_col].dt.quarter
        df_prep['day'] = df_prep[date_col].dt.day
        
        # 3. Prepare the final feature matrix X (excluding the target variable)
        target_var_in_features = [target_col]
        feature_cols_only = [f for f in all_lstm_features if f not in target_var_in_features]
        
        # Add placeholders for missing required features (like isHoliday or other features)
        for col in feature_cols_only:
            if col not in df_prep.columns:
                if df_prep.dtypes.get(col) == object:
                    df_prep[col] = 'MISSING'
                else:
                    df_prep[col] = 0.0
            # Ensure categorical columns are correctly encoded before transforming
            elif df_prep.dtypes.get(col) == object:
                 df_prep[col] = df_prep[col].astype('category').cat.codes.fillna(-1)


        # Reindex to enforce ColumnTransformer's required order
        X = df_prep.reindex(columns=feature_cols_only, fill_value=0.0)

        # If scaler exposes the exact training feature order, enforce it
        scaler_feature_order = getattr(scaler, 'feature_names_in_', None)
        if scaler_feature_order is not None and len(scaler_feature_order) > 0:
            # Ensure any absent expected columns are added with zeros
            for col in scaler_feature_order:
                if col not in X.columns:
                    X[col] = 0.0
            # Align column order exactly to scaler's expectation
            X = X.loc[:, list(scaler_feature_order)]
        
        # 4. Transform X using the loaded ColumnTransformer
        scaled_features = scaler.transform(X)
        # Ensure dense ndarray (ColumnTransformer may return sparse)
        if hasattr(scaled_features, "toarray"):
            scaled_features = scaled_features.toarray()
        elif not isinstance(scaled_features, np.ndarray):
            scaled_features = np.asarray(scaled_features)

        # 5. Reshape for LSTM (samples, time_steps, features)
        time_steps = metadata.get('time_steps', metadata.get('sequence_length', 1))
        if scaled_features.ndim == 1:
            scaled_features = scaled_features.reshape(1, -1)
        n_samples, n_features = scaled_features.shape
        if time_steps <= 1:
            scaled_final = scaled_features.reshape((n_samples, 1, n_features))
        else:
            # Repeat the last row across the required time steps
            last_row = scaled_features[-1].reshape(1, 1, n_features)
            scaled_final = np.repeat(last_row, time_steps, axis=1)
        
        # --- CHECKPOINT: PRE-PREDICTION (LSTM) ---
        try:
            print(f"\n--- CHECKPOINT 2: PRE-PREDICTION FEATURES ---")
            print(f"Model: {model_id}")
            print(f"Feature columns used: {list(X.columns)}")
            print(f"Scaled 3D shape: {scaled_final.shape}")
            print("-------------------------------------------\n")
        except Exception:
            pass
        # ----------------------------------------

        return scaled_final


    elif 'lightgbm' in model_id:
        
        df_prep = df.copy()
        
        # CRITICAL: SET INDEX FOR LAG/ROLLING CALCULATION FIRST
        df_prep = df_prep.set_index(date_col).sort_index()
        
        # 1. BASE AND TIME FEATURES
        df_prep["year"] = df_prep.index.year
        df_prep["month"] = df_prep.index.month
        df_prep["day"] = df_prep.index.day
        df_prep["dayofweek"] = df_prep.index.dayofweek
        df_prep["weekofyear"] = df_prep.index.isocalendar().week
        
        # 2. ENSURE TARGET COLUMN EXISTS (TotalRevenue)
        # The target column might be named differently in the input
        target_col_name = metadata.get('target_variable', 'TotalRevenue')
        if target_col_name not in df_prep.columns:
            # Try using the mapping target_col
            if target_col in df_prep.columns:
                df_prep[target_col_name] = df_prep[target_col]
            else:
                raise ValueError(f"Target column '{target_col_name}' not found in data")
        
        # Ensure target is numeric
        df_prep[target_col_name] = pd.to_numeric(df_prep[target_col_name], errors='coerce').fillna(0)
        
        # 3. CREATE LAG FEATURES FOR TotalRevenue (specific lags: 1, 7, 14)
        df_prep["TotalRevenue_lag_1"] = df_prep[target_col_name].shift(1).fillna(0)
        df_prep["TotalRevenue_lag_7"] = df_prep[target_col_name].shift(7).fillna(0)
        df_prep["TotalRevenue_lag_14"] = df_prep[target_col_name].shift(14).fillna(0)
        
        # 4. CREATE ROLLING STATS FOR TotalRevenue (windows: 7, 14)
        df_prep["TotalRevenue_rolling_mean_7"] = (
            df_prep[target_col_name].rolling(window=7, min_periods=1).mean().shift(1).fillna(0)
        )
        df_prep["TotalRevenue_rolling_mean_14"] = (
            df_prep[target_col_name].rolling(window=14, min_periods=1).mean().shift(1).fillna(0)
        )
        
        # 5. GET REQUIRED FEATURES FROM METADATA
        all_model_features = metadata.get('feature_names', metadata.get('required_features', [])) 
        
        # 6. HANDLE CATEGORICAL ENCODING
        categorical_cols = ['Customer', 'Location', 'BusinessType']

        training_categories: Dict[str, List[str]] = {}
        loaded_model = LOADED_MODELS.get(model_id)
        booster = getattr(loaded_model, "_Booster", None) if loaded_model is not None else None

        if booster is not None:
            try:
                booster_dump = json.loads(booster.dump_model())
                raw_categories = booster_dump.get('pandas_categorical', {})
                if isinstance(raw_categories, dict):
                    for key, categories in raw_categories.items():
                        if isinstance(categories, list):
                            training_categories[str(key)] = [str(c) for c in categories]
            except Exception:
                training_categories = {}

        for col in categorical_cols:
            if col in df_prep.columns:
                series = df_prep[col].astype(str)
                categories = training_categories.get(col)
                if categories:
                    extended_categories = categories.copy()
                    for value in series.unique():
                        if value not in extended_categories:
                            extended_categories.append(value)
                    df_prep[col] = pd.Categorical(series, categories=extended_categories, ordered=False)
                else:
                    df_prep[col] = pd.Categorical(series, ordered=False)
        
        # 7. HANDLE TARGET LEAKAGE COLUMNS
        # For prediction, we need to zero out the target column if it's in features
        # Also handle OrderCount and NumberOfPieces if they're in features but not in data
        target_fill_columns = []
        if 'TotalRevenue' in all_model_features:
            target_fill_columns.append('TotalRevenue')
        if 'OrderCount' in all_model_features and 'OrderCount' not in df_prep.columns:
            df_prep['OrderCount'] = 0
        if 'NumberOfPieces' in all_model_features and 'NumberOfPieces' not in df_prep.columns:
            df_prep['NumberOfPieces'] = 0

        # 8. FINAL REINDEXING - Select only required features
        final_input_df = df_prep.reindex(columns=all_model_features, fill_value=0)
        
        # Zero out target leakage columns for prediction
        for col in target_fill_columns:
            if col in final_input_df.columns:
                final_input_df[col] = 0

        # 9. Align to model's expected feature order if available
        model_feature_order = None
        try:
            # If the loaded model is available in the registry, fetch its feature names
            loaded_model = LOADED_MODELS.get(model_id)
            model_feature_order = getattr(loaded_model, 'feature_names_in_', None)
            # Also check if model has feature_names_ attribute (LightGBM native)
            if model_feature_order is None:
                model_feature_order = getattr(loaded_model, 'feature_name_', None)
        except Exception:
            model_feature_order = None

        if model_feature_order is not None and len(model_feature_order) > 0:
            # Add any missing columns with safe defaults (0)
            for col in model_feature_order:
                if col not in final_input_df.columns:
                    final_input_df[col] = 0
            # Avoid target leakage - zero out target column if it's in features
            if target_col_name in final_input_df.columns:
                final_input_df[target_col_name] = 0
            # Reorder columns exactly as model expects
            final_input_df = final_input_df.loc[:, list(model_feature_order)]

        # 10. Enforce numeric dtypes for model input
        # Keep categorical columns as int32 (already encoded)
        # Convert numeric columns to float32
        for col in final_input_df.columns:
            if col not in categorical_cols:
                final_input_df[col] = pd.to_numeric(final_input_df[col], errors='coerce').fillna(0).astype(np.float32)
        
        # Final cleanup
        final_input_df = final_input_df.replace([np.inf, -np.inf], 0).fillna(0)
        
        # --- DEBUG CHECKPOINT 2: BEFORE MODEL PREDICTION ---
        print(f"\n--- CHECKPOINT 2: PRE-PREDICTION FEATURES ---")
        print(f"Model: {model_id}")
        print(f"Features (final_input_df): {final_input_df.columns.tolist()}")
        print(f"Shape: {final_input_df.shape}")
        print("-------------------------------------------\n")
        # ----------------------------------------------------
        
        return final_input_df

    elif 'xgboost' in model_id or model_id == 'xgboost_v1':
        
        df_prep = df.copy()
        
        # XGBoost requires grouping by Customer-Location-BusinessType for proper lag/rolling calculations
        # First, ensure we have the required grouping columns
        grouping_cols = []
        for col in ['Customer', 'Location', 'BusinessType']:
            if col in df_prep.columns:
                grouping_cols.append(col)
        
        # Rename target column
        df_prep.rename(columns={target_col: "y"}, inplace=True)
        
        # Ensure date column is datetime
        if date_col in df_prep.columns:
            df_prep[date_col] = pd.to_datetime(df_prep[date_col], errors='coerce')
        
        # 1. TEMPORAL FEATURES (extracted from date column)
        df_prep["year"] = df_prep[date_col].dt.year
        df_prep["month"] = df_prep[date_col].dt.month
        df_prep["quarter"] = df_prep[date_col].dt.quarter
        
        # 2. SET INDEX FOR LAG/ROLLING CALCULATION
        # If we have grouping columns, we need to calculate lags/rolling per group
        if grouping_cols:
            # Sort by grouping columns and date
            df_prep = df_prep.sort_values(by=grouping_cols + [date_col])
            # Set date as index for time-based operations
            df_prep = df_prep.set_index(date_col)
            
            # Calculate lags and rolling stats per group
            lags_steps = metadata.get('lags_steps', [1, 3, 6])
            rolling_windows = metadata.get('rolling_windows', [3, 6, 12])
            
            # Group by Customer-Location-BusinessType and calculate features
            for lag in lags_steps:
                df_prep[f"lag_{lag}"] = df_prep.groupby(grouping_cols)["y"].shift(lag).fillna(0)
            
            for w in rolling_windows:
                # Calculate rolling mean per group
                roll_mean = (
                    df_prep.groupby(grouping_cols)["y"]
                    .rolling(window=w, min_periods=1)
                    .mean()
                    .shift(1)
                )
                # Reset index levels to align with original index
                roll_mean.index = roll_mean.index.droplevel(list(range(len(grouping_cols))))
                df_prep[f"roll_mean_{w}"] = roll_mean.fillna(0)
                
                # Calculate rolling std per group
                roll_std = (
                    df_prep.groupby(grouping_cols)["y"]
                    .rolling(window=w, min_periods=1)
                    .std()
                    .shift(1)
                )
                roll_std.index = roll_std.index.droplevel(list(range(len(grouping_cols))))
                df_prep[f"roll_std_{w}"] = roll_std.fillna(0)
        else:
            # No grouping columns - calculate globally
            df_prep = df_prep.set_index(date_col).sort_index()
            
            lags_steps = metadata.get('lags_steps', [1, 3, 6])
            for lag in lags_steps:
                df_prep[f"lag_{lag}"] = df_prep["y"].shift(lag).fillna(0)
            
            rolling_windows = metadata.get('rolling_windows', [3, 6, 12])
            for w in rolling_windows:
                df_prep[f"roll_mean_{w}"] = (
                    df_prep["y"].rolling(window=w, min_periods=1).mean().shift(1).fillna(0)
                )
                df_prep[f"roll_std_{w}"] = (
                    df_prep["y"].rolling(window=w, min_periods=1).std().shift(1).fillna(0)
                )
        
        # 3. GET REQUIRED FEATURES FROM METADATA
        all_model_features = metadata.get('required_features', [])
        if not all_model_features:
            # Fallback to default features if metadata doesn't specify
            all_model_features = [
                "Customer", "Location", "BusinessType", "TotalRevenue", "NumberOfPieces",
                "month", "quarter", "year",
                "lag_1", "lag_3", "lag_6",
                "roll_mean_3", "roll_std_3", "roll_mean_6", "roll_std_6",
                "roll_mean_12", "roll_std_12"
            ]
        
        # 4. HANDLE CATEGORICAL COLUMNS
        # IMPORTANT: For sklearn Pipeline with ColumnTransformer, keep categoricals as strings/objects
        # The ColumnTransformer will handle encoding. Don't convert to numeric codes here!
        categorical_cols = ['Customer', 'Location', 'BusinessType']
        for col in categorical_cols:
            if col in df_prep.columns:
                # Keep as string/object - Pipeline's ColumnTransformer will encode it
                # Only ensure it's not NaN
                df_prep[col] = df_prep[col].astype(str).fillna('Unknown')
        
        # 5. HANDLE TARGET LEAKAGE COLUMNS (TotalRevenue, NumberOfPieces should be 0 for prediction)
        target_fill_columns = []
        if 'TotalRevenue' in all_model_features:
            target_fill_columns.append('TotalRevenue')
        if 'NumberOfPieces' in all_model_features:
            target_fill_columns.append('NumberOfPieces')
        
        # 6. FINAL REINDEXING
        final_input_df = df_prep.reindex(columns=all_model_features, fill_value=np.nan)
        
        # Zero out leakage columns for prediction
        for col in target_fill_columns:
            if col in final_input_df.columns:
                final_input_df[col] = 0
        
        # 7. Align to model's expected feature order if available
        model_feature_order = None
        try:
            loaded_model = LOADED_MODELS.get(model_id)
            model_feature_order = getattr(loaded_model, 'feature_names_in_', None)
        except Exception:
            model_feature_order = None
        
        if model_feature_order is not None and len(model_feature_order) > 0:
            # Add any missing columns with safe defaults (0)
            for col in model_feature_order:
                if col not in final_input_df.columns:
                    final_input_df[col] = 0
            # Avoid target leakage
            for col in ['TotalRevenue', 'NumberOfPieces']:
                if col in final_input_df.columns:
                    final_input_df[col] = 0
            # Reorder columns exactly as model expects
            final_input_df = final_input_df.loc[:, list(model_feature_order)]
        
        # 8. Handle dtypes for model input
        # CRITICAL: For sklearn Pipeline, categorical columns must remain as strings/objects
        # Only numeric columns should be converted to float
        categorical_cols = [c for c in ['Customer', 'Location', 'BusinessType'] if c in final_input_df.columns]
        numeric_cols = [c for c in final_input_df.columns if c not in categorical_cols]
        
        # Keep categorical columns as strings (Pipeline's ColumnTransformer will encode them)
        for c in categorical_cols:
            if c in final_input_df.columns:
                # Ensure it's a string, not numeric - Pipeline expects strings for encoding
                final_input_df[c] = final_input_df[c].astype(str).fillna('Unknown')
        
        # Convert only numeric columns to float32
        for col in numeric_cols:
            try:
                final_input_df[col] = pd.to_numeric(final_input_df[col], errors='coerce').fillna(0).astype(np.float32)
            except Exception as e:
                print(f"Warning: Could not convert column {col} to float32 in prepare_data: {e}")
                final_input_df[col] = 0.0
        
        # --- DEBUG CHECKPOINT 2: BEFORE MODEL PREDICTION ---
        print(f"\n--- CHECKPOINT 2: PRE-PREDICTION FEATURES (XGBoost) ---")
        print(f"Model: {model_id}")
        print(f"Features (final_input_df): {final_input_df.columns.tolist()}")
        print(f"Shape: {final_input_df.shape}")
        print(f"Dtypes: {final_input_df.dtypes.to_dict()}")
        print("-------------------------------------------\n")
        # ----------------------------------------------------
        
        return final_input_df

    elif model_id == 'sarima_daily_v1' or 'sarima' in model_id.lower():
        # SARIMA: Prepare time series data with temporal features
        df_prep = df.copy()
        
        # Ensure date column is datetime
        if date_col in df_prep.columns:
            df_prep[date_col] = pd.to_datetime(df_prep[date_col], errors='coerce')
        
        # Set date as index for time series operations
        df_prep = df_prep.set_index(date_col).sort_index()
        
        # Extract temporal features as required by the model
        df_prep['Year'] = df_prep.index.year
        df_prep['Month'] = df_prep.index.month
        df_prep['Day'] = df_prep.index.day
        df_prep['DayOfWeek'] = df_prep.index.dayofweek
        df_prep['WeekOfYear'] = df_prep.index.isocalendar().week
        
        # Get required features from metadata
        required_features = metadata.get('required_features', [])
        
        # Ensure target column is present and numeric
        target_col_name = metadata.get('usage_notes', {}).get('target_column', target_col)
        if target_col_name not in df_prep.columns:
            # Try using the mapping target_col
            if target_col in df_prep.columns:
                df_prep[target_col_name] = df_prep[target_col]
            else:
                raise ValueError(f"Target column '{target_col_name}' not found in data")
        
        df_prep[target_col_name] = pd.to_numeric(df_prep[target_col_name], errors='coerce').fillna(0)
        
        # Select only required features (target + temporal features)
        feature_cols = [target_col_name] + [f for f in required_features if f in df_prep.columns and f != target_col_name]
        
        # Return DataFrame with date index and required columns
        df_prep = df_prep[feature_cols].dropna()
        
        return df_prep
        
    raise ValueError(f"Unknown model name for data preparation: {model_id}")

# --- Utility Function: Make Prediction ---
def make_prediction(model_id: str, model, prepared_data, horizon: int, metadata: dict, scaler=None, original_df=None):
    
    if model_id == 'prophet_weekly_v1':
        # Ensure weekly frequency for Prophet weekly model
        try:
            model.fit(prepared_data)
        except AttributeError as e:
            if 'stan_backend' in str(e):
                # Prophet version/environment mismatch - try creating a fresh instance
                from prophet import Prophet as ProphetClass
                # Recreate Prophet with same params
                hyperparams = metadata.get('default_hyperparameters', {})
                model = ProphetClass(
                    growth=hyperparams.get('growth', 'linear'),
                    seasonality_mode=hyperparams.get('seasonality_mode', 'additive'),
                    yearly_seasonality=hyperparams.get('yearly_seasonality', 'auto'),
                    weekly_seasonality=hyperparams.get('weekly_seasonality', False),
                    daily_seasonality=hyperparams.get('daily_seasonality', False)
                )
                # Try fitting again
                model.fit(prepared_data)
            else:
                raise
        except Exception as e:
            raise ValueError(f"Prophet fitting failed: {e}")
        last_ds = prepared_data['ds'].max()
        future_freq = normalize_frequency(metadata.get('freq', 'W'))
        if future_freq not in {"D", "W", "M", "Q", "Y"}:
            future_freq = "W"
        future = model.make_future_dataframe(periods=horizon, freq=future_freq)
        future = future[future['ds'] > last_ds]
        forecast = model.predict(future)
        return forecast.tail(horizon)[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

    elif model_id == 'lstm_v1':
        # LSTM: Predict the next 'horizon' steps sequentially
        scaled_data_3d = prepared_data
        
        if scaled_data_3d.shape[0] < 1:
             raise ValueError("Insufficient data for LSTM sequencing after preprocessing.")

        # Grab the last sequence from the available data
        cur = scaled_data_3d[-1:].copy() 

        preds = []
        for _ in range(horizon):
            p = model.predict(cur, verbose=0)
            # Ensure scalar
            p_scalar = float(np.asarray(p).ravel()[0])
            preds.append(p_scalar)
            # Shift sequence and append new frame with predicted target at index 0
            last_frame = cur[:, -1:, :].copy()               # shape (1,1,features)
            next_frame = last_frame.copy()
            next_frame[:, 0, 0] = p_scalar                   # assume target at index 0
            cur = np.concatenate([cur[:, 1:, :], next_frame], axis=1)

        raw_predictions = np.array(preds).flatten()
        
        # Return raw predictions to wrapper for inverse transform
        return raw_predictions
    

    elif 'lightgbm' in model_id:
        # Keep as DataFrame with correct column names; enforce numeric dtypes
        if not isinstance(prepared_data, pd.DataFrame):
            prepared_df = pd.DataFrame(prepared_data)
        else:
            prepared_df = prepared_data.copy()
        
        # Ensure categorical columns stay as int32 (LightGBM handles them better)
        categorical_cols = ['Customer', 'Location', 'BusinessType']
        for col in categorical_cols:
            if col in prepared_df.columns:
                if not pd.api.types.is_categorical_dtype(prepared_df[col]):
                    prepared_df[col] = prepared_df[col].astype("category")
                codes = prepared_df[col].cat.codes.astype(np.int32)
                # Replace unknown categories (-1) with 0 as a safe default
                prepared_df[col] = codes.where(codes >= 0, 0)
        
        # Convert numeric columns to float32
        numeric_cols = [c for c in prepared_df.columns if c not in categorical_cols]
        for col in numeric_cols:
            prepared_df[col] = pd.to_numeric(prepared_df[col], errors='coerce').fillna(0).astype(np.float32)
        
        # Final cleanup
        prepared_df = prepared_df.replace([np.inf, -np.inf], 0).fillna(0)
        
        # Check if model has feature order requirements
        model_feature_order = None
        try:
            model_feature_order = getattr(model, 'feature_names_in_', None)
            if model_feature_order is None:
                model_feature_order = getattr(model, 'feature_name_', None)
        except Exception:
            pass
        
        # Reorder columns if model expects specific order
        if model_feature_order is not None and len(model_feature_order) > 0:
            # Add missing columns
            for col in model_feature_order:
                if col not in prepared_df.columns:
                    prepared_df[col] = 0
            # Reorder to match model's expectation
            prepared_df = prepared_df[list(model_feature_order)]
        
        predictions = model.predict(prepared_df)
        out_df = pd.DataFrame({'date': prepared_df.index.values, 'prediction': predictions})

    
        # --- DEBUG CHECKPOINT 3: POST-PREDICTION OUTPUT ---
        print(f"\n--- CHECKPOINT 3: MODEL OUTPUT ---")
        print(f"Model: {model_id}")
        print(f"Output Columns: {out_df.columns.tolist()}")
        print("----------------------------------\n")
        # ------------------------------------------
        
        return out_df

    elif 'xgboost' in model_id or model_id == 'xgboost_v1':
        # XGBoost: Similar to LightGBM but handle DataFrame properly
        if not isinstance(prepared_data, pd.DataFrame):
            prepared_df = pd.DataFrame(prepared_data)
        else:
            prepared_df = prepared_data.copy()
        
        # Ensure all columns are numeric - handle categorical/object types explicitly
        for col in prepared_df.columns:
            if prepared_df[col].dtype == 'object' or prepared_df[col].dtype.name == 'category':
                # Convert categorical/object to numeric
                if prepared_df[col].dtype.name == 'category':
                    prepared_df[col] = prepared_df[col].cat.codes
                prepared_df[col] = pd.to_numeric(prepared_df[col], errors='coerce').fillna(0)
        
        # Convert all to numeric and handle inf/nan
        prepared_df = prepared_df.apply(pd.to_numeric, errors='coerce').replace([np.inf, -np.inf], 0).fillna(0)
        prepared_df.columns = prepared_df.columns.astype(str)
        
        # Final conversion to float32 - ensure ALL columns are numeric
        for col in prepared_df.columns:
            # Force conversion to numeric, handling any edge cases
            try:
                # First try direct conversion
                if prepared_df[col].dtype == 'object' or str(prepared_df[col].dtype).startswith('category'):
                    # Convert categorical/object to numeric codes first
                    if hasattr(prepared_df[col], 'cat'):
                        prepared_df[col] = prepared_df[col].cat.codes
                    prepared_df[col] = pd.to_numeric(prepared_df[col], errors='coerce')
                
                # Convert to float32
                prepared_df[col] = pd.to_numeric(prepared_df[col], errors='coerce').fillna(0).astype(np.float32)
            except Exception as e:
                # If all else fails, set to zero
                prepared_df[col] = 0.0
                print(f"Warning: Could not convert column {col} to float32, setting to 0.0. Error: {e}")
        
        # Check if it's a sklearn Pipeline FIRST - this determines our approach
        # For Pipeline models, we need to preserve categorical columns as strings
        # For non-Pipeline models, we'll convert everything to numeric
        from sklearn.pipeline import Pipeline
        is_pipeline = isinstance(model, Pipeline)
        
        if is_pipeline:
            # For Pipeline models, work directly with the original DataFrame
            # Don't convert to numpy - we need to preserve categorical columns as strings
            print("Model is a sklearn Pipeline - will use DataFrame with proper column names")
            prepared_df_clean = prepared_data.copy()
            
            # Ensure categorical columns are strings (they should already be from prepare_data)
            categorical_cols = [c for c in ['Customer', 'Location', 'BusinessType'] if c in prepared_df_clean.columns]
            for col in categorical_cols:
                if col in prepared_df_clean.columns:
                    prepared_df_clean[col] = prepared_df_clean[col].astype(str).fillna('Unknown')
            
            # Ensure numeric columns are float64
            numeric_cols = [c for c in prepared_df_clean.columns if c not in categorical_cols]
            for col in numeric_cols:
                prepared_df_clean[col] = pd.to_numeric(prepared_df_clean[col], errors='coerce').fillna(0).astype(np.float64)
            
            # Ensure index is simple integer range
            prepared_df_clean.reset_index(drop=True, inplace=True)
        else:
            # For non-Pipeline models, convert to numpy array for XGBoost prediction
            try:
                # Convert DataFrame to numpy array - use float64 as XGBoost often prefers it
                np_array = prepared_df.values.astype(np.float64)
                
                # Clean any NaN, inf, or problematic values BEFORE prediction
                np_array = np.nan_to_num(np_array, nan=0.0, posinf=0.0, neginf=0.0)
                
                # Ensure array is contiguous and in C-order (required by some XGBoost versions)
                np_array = np.ascontiguousarray(np_array, dtype=np.float64)
                
                print(f"Successfully converted to numpy array. Shape: {np_array.shape}, dtype: {np_array.dtype}")
                print(f"Array has NaN: {np.isnan(np_array).any()}, has Inf: {np.isinf(np_array).any()}")
            except Exception as e:
                print(f"ERROR converting to numpy array: {e}")
                print(f"DataFrame dtypes: {prepared_df.dtypes}")
                raise ValueError(f"Cannot convert DataFrame to numeric array. Some columns are not numeric: {e}")
            
            # XGBoost prediction - check if model expects DataFrame with feature names
            # XGBoost models trained with DataFrames remember feature names and may require them
            model_feature_names = None
            try:
                # Check if model has feature_names_in_ attribute (sklearn-style)
                model_feature_names = getattr(model, 'feature_names_in_', None)
                if model_feature_names is not None:
                    print(f"Model expects features: {list(model_feature_names)}")
            except Exception:
                pass
            
            # Create a completely fresh DataFrame with no index issues
            # Convert to numpy first, clean it, then create new DataFrame
            np_clean = prepared_df.values.astype(np.float64)
            np_clean = np.nan_to_num(np_clean, nan=0.0, posinf=0.0, neginf=0.0)
            np_clean = np.ascontiguousarray(np_clean, dtype=np.float64)
            
            # Get column names in correct order
            if model_feature_names is not None:
                # Use model's expected feature order
                col_names = list(model_feature_names)
                # Ensure all expected columns are present
                missing_cols = set(col_names) - set(prepared_df.columns)
                if missing_cols:
                    print(f"Warning: Missing columns {missing_cols}, will add zeros")
                    # Add missing columns to numpy array
                    missing_data = np.zeros((np_clean.shape[0], len(missing_cols)), dtype=np.float64)
                    np_clean = np.hstack([np_clean, missing_data])
                    # Update column names
                    all_cols = list(prepared_df.columns) + list(missing_cols)
                    # Reorder to match model's expected order
                    col_order = [c for c in col_names if c in all_cols]
                    # Reorder numpy array columns
                    col_indices = [all_cols.index(c) for c in col_order]
                    np_clean = np_clean[:, col_indices]
                    col_names = col_order
                else:
                    # Reorder columns to match model's expected order
                    col_indices = [prepared_df.columns.get_loc(c) for c in col_names]
                    np_clean = np_clean[:, col_indices]
            else:
                col_names = list(prepared_df.columns)
            
            # Create completely fresh DataFrame with simple integer index
            prepared_df_clean = pd.DataFrame(
                np_clean, 
                columns=col_names,
                dtype=np.float64
            )
            
            # Ensure index is simple integer range
            prepared_df_clean.reset_index(drop=True, inplace=True)
        
        # Common debug output for both paths
        print(f"DataFrame dtypes before prediction: {prepared_df_clean.dtypes.to_dict()}")
        print(f"DataFrame shape: {prepared_df_clean.shape}")
        print(f"DataFrame index type: {type(prepared_df_clean.index)}")
        
        # Debug: Check model type
        print(f"Model type: {type(model)}")
        print(f"Model attributes: {[attr for attr in dir(model) if not attr.startswith('_')][:10]}")
        
        if is_pipeline:
            try:
                # Inspect pipeline steps
                if hasattr(model, 'steps'):
                    print(f"Pipeline has {len(model.steps)} steps:")
                    for i, (step_name, step_transformer) in enumerate(model.steps):
                        print(f"  Step {i}: {step_name} -> {type(step_transformer).__name__}")
                    
                    # Pipelines typically expect DataFrames with column names matching training data
                    # Get feature names from pipeline if available
                    pipeline_feature_names = None
                    try:
                        if hasattr(model, 'feature_names_in_'):
                            pipeline_feature_names = model.feature_names_in_
                            print(f"Pipeline expects features: {list(pipeline_feature_names)}")
                        # Also try to get feature names from the first transformer if available
                        if pipeline_feature_names is None and hasattr(model, 'steps') and len(model.steps) > 0:
                            first_transformer = model.steps[0][1]
                            if hasattr(first_transformer, 'feature_names_in_'):
                                pipeline_feature_names = first_transformer.feature_names_in_
                                print(f"Pipeline first step expects features: {list(pipeline_feature_names)}")
                    except Exception as e:
                        print(f"Could not get pipeline feature names: {e}")
                    
                    # Ensure DataFrame columns match what pipeline expects
                    if pipeline_feature_names is not None:
                        # Reorder and add missing columns
                        missing_cols = set(pipeline_feature_names) - set(prepared_df_clean.columns)
                        if missing_cols:
                            print(f"Adding missing columns to match pipeline: {missing_cols}")
                            for col in missing_cols:
                                prepared_df_clean[col] = 0.0
                        # Reorder to match pipeline's expected order
                        prepared_df_clean = prepared_df_clean[list(pipeline_feature_names)]
                        print(f"DataFrame columns reordered to match pipeline: {list(prepared_df_clean.columns)}")
                
                # Try different prediction methods
                predictions = None
                prediction_method = None
                
                # Method 1: Try with DataFrame (Pipelines typically require DataFrames)
                try:
                    # CRITICAL: For sklearn Pipeline, we need to preserve categorical columns as strings
                    # Don't convert everything to numpy - keep the original DataFrame structure
                    pipeline_df = prepared_df_clean.copy()
                    
                    # Identify categorical vs numeric columns
                    categorical_cols = [c for c in ['Customer', 'Location', 'BusinessType'] if c in pipeline_df.columns]
                    numeric_cols = [c for c in pipeline_df.columns if c not in categorical_cols]
                    
                    # Ensure categorical columns are strings (Pipeline's ColumnTransformer expects this)
                    for col in categorical_cols:
                        if col in pipeline_df.columns:
                            # Convert to string, handling any numeric values that might have been created
                            pipeline_df[col] = pipeline_df[col].astype(str).fillna('Unknown')
                            # Replace any numeric string representations with actual category names if needed
                            # (e.g., if we have "0", "1", "2" from previous encoding, we might need original values)
                            # For now, keep as strings - the encoder will handle unknown categories
                    
                    # Convert only numeric columns to float64
                    for col in numeric_cols:
                        # Convert to numpy, clean, then back to Series
                        col_values = pipeline_df[col].values
                        col_values = np.asarray(col_values, dtype=np.float64)
                        col_values = np.nan_to_num(col_values, nan=0.0, posinf=0.0, neginf=0.0)
                        pipeline_df[col] = pd.Series(col_values, dtype=np.float64)
                    
                    # Ensure index is simple integer range
                    pipeline_df.reset_index(drop=True, inplace=True)
                    
                    # Final verification
                    print(f"Pipeline DataFrame dtypes: {pipeline_df.dtypes.to_dict()}")
                    print(f"Pipeline DataFrame has NaN: {pipeline_df.isna().any().any()}")
                    print(f"Pipeline DataFrame shape: {pipeline_df.shape}")
                    
                    # Try prediction with Pipeline
                    # If pipeline has steps, we can debug by applying them one by one
                    if hasattr(model, 'steps') and len(model.steps) > 1:
                        print("Applying pipeline steps individually for debugging...")
                        X_current = pipeline_df.copy()
                        for i, (step_name, step_transformer) in enumerate(model.steps[:-1]):
                            try:
                                print(f"  Applying step {i} ({step_name}): {type(step_transformer).__name__}")
                                X_current = step_transformer.transform(X_current)
                                print(f"    Output shape: {X_current.shape}, dtype: {type(X_current)}")
                            except Exception as step_error:
                                print(f"    ERROR in step {i} ({step_name}): {step_error}")
                                raise step_error
                        
                        # Final prediction step
                        final_estimator = model.steps[-1][1]
                        print(f"  Final prediction with: {type(final_estimator).__name__}")
                        predictions = final_estimator.predict(X_current)
                    else:
                        # Single step or no steps - direct prediction
                        predictions = model.predict(pipeline_df)
                    
                    prediction_method = "pipeline_dataframe"
                    print(f"Prediction successful with sklearn Pipeline (DataFrame). Predictions shape: {predictions.shape}")
                except Exception as e_df:
                    print(f"DataFrame prediction with Pipeline failed: {e_df}")
                    import traceback
                    print(f"Full traceback: {traceback.format_exc()}")
                    
                    # Method 2: Try with numpy array (some pipelines accept this)
                    try:
                        # Use the cleaned numpy array
                        predictions = model.predict(np_clean)
                        prediction_method = "pipeline_numpy"
                        print(f"Prediction successful with sklearn Pipeline (numpy). Predictions shape: {predictions.shape}")
                    except Exception as e_np:
                        print(f"Numpy array prediction with Pipeline failed: {e_np}")
                        
                        # Method 3: If pipeline has XGBoost as final step, try to access it
                        if is_pipeline and XGBOOST_AVAILABLE:
                            try:
                                # Get the last step (usually the estimator)
                                last_step = model.steps[-1][1] if hasattr(model, 'steps') else None
                                if last_step is not None:
                                    print(f"Pipeline last step: {type(last_step)}")
                                    # Try to get booster from the last step
                                    booster = None
                                    if hasattr(last_step, 'get_booster'):
                                        booster = last_step.get_booster()
                                    elif hasattr(last_step, 'booster'):
                                        booster = last_step.booster
                                    
                                    if booster is not None:
                                        # Transform data through pipeline steps except last
                                        if len(model.steps) > 1:
                                            # Apply all steps except the last (the estimator)
                                            X_transformed = prepared_df_clean
                                            for step_name, step_transformer in model.steps[:-1]:
                                                X_transformed = step_transformer.transform(X_transformed)
                                            # Now predict with booster
                                            dmatrix = xgb.DMatrix(data=X_transformed.values, feature_names=list(X_transformed.columns))
                                            predictions = booster.predict(dmatrix)
                                        else:
                                            dmatrix = xgb.DMatrix(data=np_clean, feature_names=col_names)
                                            predictions = booster.predict(dmatrix)
                                        prediction_method = "pipeline_booster"
                                        print(f"Prediction successful with Pipeline's XGBoost booster. Predictions shape: {predictions.shape}")
                                    else:
                                        raise ValueError("Could not access booster from pipeline's last step")
                                else:
                                    raise ValueError("Could not access pipeline steps")
                            except Exception as e_booster:
                                print(f"Pipeline booster method failed: {e_booster}")
                                raise ValueError(f"All prediction methods failed. DataFrame: {e_df}, Numpy: {e_np}, Booster: {e_booster}")
                        else:
                            raise ValueError(f"All prediction methods failed. DataFrame: {e_df}, Numpy: {e_np}")
                
                if predictions is None:
                    raise ValueError("Failed to get predictions from any method")
                
                # Ensure predictions is 1D array
                predictions = np.asarray(predictions).flatten()
                print(f"Predictions shape after flattening: {predictions.shape}, length: {len(predictions)}")
                
                # Determine how many predictions we actually have
                num_predictions = len(predictions)
                
                # Create output DataFrame with dates and predictions
                # For XGBoost, we need to generate future dates based on the last date in the data
                # Try to get last date from multiple sources
                last_date = None
                
                # First, try to get from prepared_data index if it's a DatetimeIndex
                if hasattr(prepared_data, 'index') and len(prepared_data.index) > 0:
                    if isinstance(prepared_data.index, pd.DatetimeIndex):
                        last_date = prepared_data.index[-1]
                
                # If not found, try to get from original_df
                if last_date is None and original_df is not None:
                    # Try to find date column - check common names or metadata
                    date_col_name = None
                    if hasattr(original_df, 'columns'):
                        # Try common date column names
                        for col_name in ['date', 'Date', 'DATE', 'WorkDate', 'workdate', 'ds']:
                            if col_name in original_df.columns:
                                date_col_name = col_name
                                break
                        # If not found, try to get from metadata
                        if date_col_name is None and 'date_col' in metadata:
                            date_col_name = metadata['date_col']
                        
                        if date_col_name and date_col_name in original_df.columns:
                            last_date = pd.to_datetime(original_df[date_col_name].max())
                
                # If still not found, use current time as fallback
                if last_date is None:
                    last_date = pd.Timestamp.now()
                
                if hasattr(prepared_data, 'index') and len(prepared_data.index) > 0:
                    
                    freq = metadata.get('freq', 'ME')
                    # Normalize to pandas-friendly codes (ME/QE/YE -> M/Q/Y)
                    freq = normalize_frequency(freq)
                    # Fallback to M if still invalid
                    if freq not in {"D", "W", "M", "Q", "Y"}:
                        freq = "M"
                    
                    # Generate future dates - ensure we generate exactly num_predictions dates
                    # If predictions are for all input rows, we only want the last 'horizon' predictions
                    if num_predictions > horizon:
                        # Model predicted for all input rows, we only want future predictions
                        # Take the last 'horizon' predictions
                        predictions = predictions[-horizon:]
                        num_predictions = horizon
                    
                    # Generate exactly num_predictions future dates
                    future_dates = pd.date_range(start=last_date, periods=num_predictions + 1, freq=freq)[1:]
                    
                    # Ensure both arrays have the same length
                    min_len = min(len(future_dates), len(predictions))
                    out_df = pd.DataFrame({
                        'date': future_dates[:min_len],
                        'prediction': predictions[:min_len]
                    })
                else:
                    # Fallback: use index values or create sequential dates
                    # Ensure we have matching lengths
                    if hasattr(prepared_df, 'index') and len(prepared_df.index) > 0:
                        date_values = prepared_df.index.values[:num_predictions]
                    else:
                        # Create sequential dates as fallback
                        date_values = pd.date_range(start=pd.Timestamp.now(), periods=num_predictions, freq='D')
                    
                    min_len = min(len(date_values), len(predictions))
                    out_df = pd.DataFrame({
                        'date': date_values[:min_len],
                        'prediction': predictions[:min_len]
                    })
                
                # --- DEBUG CHECKPOINT 3: POST-PREDICTION OUTPUT ---
                print(f"\n--- CHECKPOINT 3: MODEL OUTPUT (XGBoost) ---")
                print(f"Model: {model_id}")
                print(f"Output Columns: {out_df.columns.tolist()}")
                print(f"Predictions shape: {out_df.shape}")
                print("----------------------------------\n")
                # ------------------------------------------
                
                return out_df
            except Exception as e1:
                print(f"XGBoost Pipeline prediction failed: {e1}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                raise ValueError(f"XGBoost prediction failed: {e1}")
    
    elif model_id == 'sarima_daily_v1' or 'sarima' in model_id.lower():
        # SARIMA: Use statsmodels SARIMAX forecast method
        try:
            from statsmodels.tsa.statespace.sarimax import SARIMAXResults
            
            # Get target column name from metadata
            target_col_name = metadata.get('usage_notes', {}).get('target_column', 'TotalRevenue')
            
            # Extract the target time series
            if target_col_name in prepared_data.columns:
                target_series = prepared_data[target_col_name]
            else:
                # Fallback: use first numeric column
                numeric_cols = prepared_data.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    target_series = prepared_data[numeric_cols[0]]
                else:
                    raise ValueError(f"Could not find target column '{target_col_name}' in prepared data")
            
            # Ensure target_series is a pandas Series with DatetimeIndex
            if not isinstance(target_series, pd.Series):
                target_series = pd.Series(target_series)
            
            # Ensure the series is sorted by index
            if hasattr(target_series, 'index'):
                target_series = target_series.sort_index()
            
            # Extract exogenous variables (exog) if they exist in prepared_data
            # These are the features like Year, Month, Day, DayOfWeek, WeekOfYear
            exog_vars = None
            required_features = metadata.get('required_features', [])
            exog_feature_names = [f for f in required_features if f != target_col_name]
            
            if exog_feature_names and len(exog_feature_names) > 0:
                # Check if exogenous variables are in prepared_data
                available_exog = [f for f in exog_feature_names if f in prepared_data.columns]
                if available_exog:
                    exog_vars = prepared_data[available_exog].copy()
                    # Ensure exog_vars is sorted by index to match target_series
                    if hasattr(exog_vars, 'index'):
                        exog_vars = exog_vars.sort_index()
                    # CRITICAL: Convert all columns to numeric types
                    for col in exog_vars.columns:
                        exog_vars[col] = pd.to_numeric(exog_vars[col], errors='coerce').fillna(0).astype(np.int64 if col in ['Year', 'Month', 'Day', 'DayOfWeek', 'WeekOfYear'] else np.float64)
            
            # Generate future dates for forecast
            last_date = target_series.index[-1] if hasattr(target_series, 'index') and len(target_series.index) > 0 else pd.Timestamp.now()
            freq = metadata.get('freq', 'D')
            future_dates = pd.date_range(start=last_date, periods=horizon + 1, freq=freq)[1:]
            
            # Generate future exogenous variables if needed
            future_exog = None
            if exog_vars is not None and len(exog_vars.columns) > 0:
                # Create future exogenous variables based on future dates
                future_exog_df = pd.DataFrame(index=future_dates)
                for col in exog_vars.columns:
                    if col == 'Year':
                        future_exog_df[col] = future_dates.year.astype(np.int64)
                    elif col == 'Month':
                        future_exog_df[col] = future_dates.month.astype(np.int64)
                    elif col == 'Day':
                        future_exog_df[col] = future_dates.day.astype(np.int64)
                    elif col == 'DayOfWeek':
                        future_exog_df[col] = future_dates.dayofweek.astype(np.int64)
                    elif col == 'WeekOfYear':
                        future_exog_df[col] = future_dates.isocalendar().week.astype(np.int64)
                    else:
                        # For other features, use the last known value or 0
                        last_value = exog_vars[col].iloc[-1] if len(exog_vars) > 0 else 0
                        future_exog_df[col] = pd.to_numeric([last_value] * len(future_dates), errors='coerce').fillna(0).astype(np.float64)
                
                # Ensure column order matches the original exog_vars
                future_exog = future_exog_df[exog_vars.columns]
                # CRITICAL: Ensure all columns are numeric
                for col in future_exog.columns:
                    if col in ['Year', 'Month', 'Day', 'DayOfWeek', 'WeekOfYear']:
                        future_exog[col] = future_exog[col].astype(np.int64)
                    else:
                        future_exog[col] = pd.to_numeric(future_exog[col], errors='coerce').fillna(0).astype(np.float64)
            
            # For SARIMAX models with exogenous variables:
            # 1. Update model with new data using apply() with exog
            # 2. Forecast with future exog values
            
            try:
                if len(target_series) > 0:
                    # Update model with new observations and exogenous variables
                    if exog_vars is not None:
                        # Ensure exog_vars is a numpy array with proper dtype
                        exog_array = exog_vars.values.astype(np.float64)
                        updated_model = model.apply(target_series, exog=exog_array)
                    else:
                        updated_model = model.apply(target_series)
                    
                    # Forecast with future exogenous variables if available
                    if future_exog is not None:
                        # Ensure future_exog is a numpy array with proper dtype
                        future_exog_array = future_exog.values.astype(np.float64)
                        forecast_result = updated_model.get_forecast(steps=horizon, exog=future_exog_array)
                    else:
                        forecast_result = updated_model.get_forecast(steps=horizon)
                else:
                    # No new data, use original model
                    if future_exog is not None:
                        # Ensure future_exog is a numpy array with proper dtype
                        future_exog_array = future_exog.values.astype(np.float64)
                        forecast_result = model.get_forecast(steps=horizon, exog=future_exog_array)
                    else:
                        forecast_result = model.get_forecast(steps=horizon)
            except (AttributeError, TypeError) as e:
                # If apply() doesn't work, try direct forecast
                if future_exog is not None:
                    # Ensure future_exog is a numpy array with proper dtype
                    future_exog_array = future_exog.values.astype(np.float64)
                    forecast_result = model.get_forecast(steps=horizon, exog=future_exog_array)
                else:
                    forecast_result = model.get_forecast(steps=horizon)
            
            # Extract forecast values and confidence intervals
            forecast_mean = forecast_result.predicted_mean
            forecast_ci = forecast_result.conf_int()
            
            # Create output DataFrame
            out_df = pd.DataFrame({
                'date': future_dates[:len(forecast_mean)],
                'prediction': forecast_mean.values,
                'yhat_lower': forecast_ci.iloc[:, 0].values if len(forecast_ci.columns) > 0 else forecast_mean.values,
                'yhat_upper': forecast_ci.iloc[:, 1].values if len(forecast_ci.columns) > 1 else forecast_mean.values
            })
            
            return out_df
            
        except ImportError:
            raise ImportError("statsmodels is required for SARIMA predictions. Install with: pip install statsmodels")
        except Exception as e:
            raise ValueError(f"SARIMA prediction failed: {e}")
    
    raise ValueError(f"Unknown model name for prediction: {model_id}")


# --- Initialization Logic ---
def initialize_models():
    """Loads all models and assets on startup."""
    global LOADED_MODELS, LOADED_SCALERS
    print("--- Initializing Forecasting Core Models ---")
    for model_id, config in MODEL_CONFIGS.items():
        try:
            model, metadata = load_model_and_metadata(
                model_id, 
                config['model_path'], 
                config['metadata_path']
            )
            
            scaler = None
            if model_id == 'lstm_v1':
                 scaler_path = config.get('scaler_path')
                 if scaler_path and os.path.exists(scaler_path):
                     with open(scaler_path, "rb") as f:
                         scaler = pickle.load(f)
                     LOADED_SCALERS[model_id] = scaler
                 else:
                     print(f"CRITICAL: LSTM scaler not found at {scaler_path}. Skipping model.")
                     continue

            LOADED_MODELS[model_id] = model
            LOADED_MODELS[model_id + '_metadata'] = {**config, **metadata} 
            print(f"Loaded {model_id}")
        except Exception as e:
            print(f"Error loading {model_id}: {e}")
    print("--- Model initialization complete ---")

initialize_models()


# --------------------------------------------------------------
# 2. API WRAPPER FUNCTIONS (FINAL FIXES)
# --------------------------------------------------------------

def _get_model_assets(model_id: str):
    model = LOADED_MODELS.get(model_id)
    metadata = LOADED_MODELS.get(model_id + '_metadata')
    scaler = LOADED_SCALERS.get(model_id)
    if model is None: raise ValueError(f"Model {model_id} not loaded.")
    return model, metadata, scaler


def predict_prophet(df: pd.DataFrame, mapping: ColumnMapping, horizon: int):
    model_id = 'prophet_weekly_v1'
    _, metadata, _ = _get_model_assets(model_id)
    
    # Check if cmdstanpy is available (required for Prophet)
    try:
        import cmdstanpy
        # Verify cmdstan is installed
        try:
            cmdstanpy.find_cmdstan()
        except Exception:
            raise ValueError(
                "Prophet requires cmdstanpy with cmdstan installed. "
                "Install with: pip install cmdstanpy && python -c 'import cmdstanpy; cmdstanpy.install_cmdstan()'"
            )
    except ImportError:
        raise ValueError(
            "Prophet requires cmdstanpy to be installed. "
            "Add 'cmdstanpy>=1.0.0' to requirements.txt and rebuild the container."
        )
    
    hyperparams = metadata.get('default_hyperparameters', {})
    
    # Create Prophet model - errors will be caught in make_prediction
    m = Prophet(
        growth=hyperparams.get('growth', 'linear'),
        seasonality_mode=hyperparams.get('seasonality_mode', 'additive'),
        yearly_seasonality=hyperparams.get('yearly_seasonality', 'auto'),
        weekly_seasonality=hyperparams.get('weekly_seasonality', False),
        daily_seasonality=hyperparams.get('daily_seasonality', False)
    )

    prepared_data = prepare_data(model_id, df, mapping, metadata)
    predictions = make_prediction(model_id, m, prepared_data, horizon, metadata) 
    
    return predictions.rename(columns={'ds': 'date', 'yhat': 'prediction'})



def predict_lstm(df: pd.DataFrame, mapping: ColumnMapping, horizon: int):
    model_id = 'lstm_v1'
    model, metadata, scaler = _get_model_assets(model_id)
    
    scaled_data_3d = prepare_data(model_id, df, mapping, metadata, scaler)
    raw_predictions = make_prediction(model_id, model, scaled_data_3d, horizon, metadata, scaler)
    
    # --- FINAL FIX: Apply inverse of target transform only ---
    # Model was trained on log-transformed target; features were scaled by ColumnTransformer
    # We do NOT inverse-transform features; we only invert the target transform.
    final_predictions = np.exp(np.asarray(raw_predictions).ravel())
    # --- END FINAL FIX ---
    
    last_date = pd.to_datetime(df[mapping.date_col].max())
    freq = metadata.get('freq', 'D')
    dates = pd.date_range(start=last_date, periods=horizon + 1, freq=freq)[1:]

    return pd.DataFrame({"date": dates, "prediction": final_predictions.flatten()})

def predict_lightgbm(df: pd.DataFrame, mapping: ColumnMapping, horizon: int, model_id: str):
    """Handles both lightgbm_model"""
    
    if model_id not in ['lightgbm_model']:
        raise ValueError(f"Invalid LightGBM model ID: {model_id}")
        
    model, metadata, _ = _get_model_assets(model_id)
    
    prepared_data = prepare_data(model_id, df, mapping, metadata)
    predictions_df = make_prediction(model_id, model, prepared_data, horizon, metadata)
    
    out = df.tail(horizon).copy()
    out.rename(columns={mapping.target_col: "target_value", mapping.date_col: "date"}, inplace=True)
    out['prediction'] = predictions_df['prediction'].tail(horizon).values

    return out[['date', 'target_value', 'prediction']]

def predict_xgboost(df: pd.DataFrame, mapping: ColumnMapping, horizon: int, model_id: str = 'xgboost_v1'):
    """Handles XGBoost model predictions"""
    
    if model_id not in ['xgboost_v1']:
        raise ValueError(f"Invalid XGBoost model ID: {model_id}")
        
    model, metadata, _ = _get_model_assets(model_id)
    
    prepared_data = prepare_data(model_id, df, mapping, metadata)
    predictions_df = make_prediction(model_id, model, prepared_data, horizon, metadata, original_df=df)
    
    # XGBoost returns predictions with dates already included from make_prediction
    # Just return the predictions DataFrame as-is (it already has dates and predictions)
    # Ensure the output has the correct columns and matching lengths
    if 'date' in predictions_df.columns and 'prediction' in predictions_df.columns:
        # Ensure both columns have the same length
        min_len = min(len(predictions_df['date']), len(predictions_df['prediction']))
        out = pd.DataFrame({
            'date': predictions_df['date'].values[:min_len],
            'prediction': predictions_df['prediction'].values[:min_len]
        })
    else:
        # Fallback: create dates if not present
        last_date = pd.to_datetime(df[mapping.date_col].max())
        # Normalize to pandas-friendly codes (no *E aliases)
        freq = normalize_frequency(metadata.get('freq', 'M'))
        if freq not in {"D", "W", "M", "Q", "Y"}:
            freq = "M"
        future_dates = pd.date_range(start=last_date, periods=horizon + 1, freq=freq)[1:]
        
        predictions = predictions_df['prediction'].values if 'prediction' in predictions_df.columns else predictions_df.values.flatten()
        min_len = min(len(future_dates), len(predictions))
        out = pd.DataFrame({
            'date': future_dates[:min_len],
            'prediction': predictions[:min_len]
        })
    
    return out

def predict_sarima(df: pd.DataFrame, mapping: ColumnMapping, horizon: int):
    """Handles SARIMA model predictions"""
    
    model_id = 'sarima_daily_v1'
    model, metadata, _ = _get_model_assets(model_id)
    
    prepared_data = prepare_data(model_id, df, mapping, metadata)
    predictions_df = make_prediction(model_id, model, prepared_data, horizon, metadata)
    
    # SARIMA returns DataFrame with date, prediction, yhat_lower, yhat_upper
    # Standardize to just date and prediction for consistency
    if 'date' in predictions_df.columns and 'prediction' in predictions_df.columns:
        out = pd.DataFrame({
            'date': predictions_df['date'],
            'prediction': predictions_df['prediction']
        })
    else:
        # Fallback if structure is different
        out = predictions_df.copy()
    
    return out


# --------------------------------------------------------------
# 3. FASTAPI APPLICATION 
# --------------------------------------------------------------

app = FastAPI(
    title="Supply Chain Forecasting API",
    description="Prophet • LSTM • LightGBM with dynamic mapping",
    version="2.0.4",
)
log = logging.getLogger("uvicorn")

# --- Request / Response models ---
class PredictionRequestItem(BaseModel):
    model_name: str
    column_mapping: ColumnMapping
    data: List[Dict[str, Any]]
    horizon_steps: int
    frequency: str = Field(..., example="M")

class PredictionRequest(BaseModel):
    items: List[PredictionRequestItem]

class PredictionResponseItem(BaseModel):
    model_name: str
    status: str
    prediction: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

# --- Helper: load & validate schema (from main.py) ---
VALID_FREQUENCIES = {"D", "W", "M", "Q", "Y", "ME", "QE", "YE"}

def normalize_frequency(freq: str) -> str:
    """Normalize user/model-provided frequency aliases to pandas-friendly codes."""
    if not isinstance(freq, str):
        return "D"
    freq = freq.strip().upper()
    alias_map = {
        "ME": "M",   # month-end -> monthly
        "QE": "Q",   # quarter-end -> quarterly
        "YE": "Y",   # year-end -> yearly
    }
    return alias_map.get(freq, freq)

def load_schema(model_name: str) -> dict:
    # Try models directory first
    path = os.path.join(BASE_DIR, "knowledge_base", "models", f"{model_name}_schema.json")
    if not os.path.exists(path):
        # Try schemas directory
        path = os.path.join(BASE_DIR, "knowledge_base", "schemas", f"{model_name}_schema.json")
        # Also try with sarimax name for SARIMA models
        if not os.path.exists(path) and 'sarima' in model_name.lower():
            path = os.path.join(BASE_DIR, "knowledge_base", "schemas", "sarimax_schema.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Schema not found for {model_name}. Tried: {path}") 
    with open(path, "r") as f:
        return json.load(f)

def validate_schema(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Very light validation + auto-fill of optional columns."""
    for purpose, info in schema.get("required_columns_by_purpose", {}).items():
        col = info.get("source", purpose)
        if col not in df.columns:
            raise ValueError(f"Missing required column for {purpose}: {col}")
        if info.get("expected_type") == "numeric":
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if schema.get("dynamic_properties", {}).get("auto_fill_missing"):
        for opt, oinfo in schema.get("optional_columns_by_purpose", {}).items():
            col = oinfo.get("source", opt)
            if col not in df.columns:
                df[col] = 0 if oinfo.get("expected_type") == "numeric" else "Unknown"
    return df


# --- Endpoints ---
@app.get("/")
def root():
    return {"message": "Supply Chain Forecasting API v2.0 – /docs"}

@app.get("/health")
def health_check():
    """Health check endpoint for Docker and monitoring"""
    return {
        "status": "healthy",
        "models_loaded": len(LOADED_MODELS),
        "timestamp": datetime.now().isoformat(),
        "service": "forecast-api"
    }

# CODE from unified_forecaster_app.py (Final Corrected predict_endpoint)

# CODE from unified_forecaster_app.py (Final Corrected predict_endpoint)

@app.post("/predict", response_model=List[PredictionResponseItem])
async def predict_endpoint(req: PredictionRequest):
    results: List[PredictionResponseItem] = []

    for itm in req.items:
        model = itm.model_name
        mapping = itm.column_mapping
        horizon = itm.horizon_steps
        freq = itm.frequency

        try:
            # ---- 1. Raw → clean DataFrame ---------------------------------
            df = pd.DataFrame(itm.data)

            # ---- 2. Schema validation (omitted) -------------------------
            try:
                # ... (load_schema and validate_schema calls) ...
                sch = load_schema(model)
                df = validate_schema(df, sch)
            except Exception as sch_err:
                pass # Suppress warning for clean output

            # ---- 3. Clean target & date ----------------------------------
            df[mapping.target_col] = (
                df[mapping.target_col]
                .astype(str)
                .str.replace(r"[^\d.]", "", regex=True)
            )
            df[mapping.target_col] = pd.to_numeric(
                df[mapping.target_col], errors="coerce"
            )
            df[mapping.date_col] = pd.to_datetime(
                df[mapping.date_col], errors="coerce"
            )
            df = df.dropna(subset=[mapping.date_col, mapping.target_col])

            if df.empty:
                raise ValueError("Data empty after cleaning.")

            # --- CRITICAL FIX 1: TEMPORAL FEATURES ARE NOT GENERATED HERE ---
            
            # ---- 4. Aggregation (resample) -------------------------------
            df = df.set_index(mapping.date_col).sort_index()

            agg_map = {mapping.target_col: "sum"}
            
            model_id = model
            metadata = LOADED_MODELS.get(model_id + '_metadata', {})
            all_model_features = metadata.get('required_features', []) 
            
            TEMPORAL_COLS = ['year', 'month', 'quarter', 'dayofweek', 'day']

            # FIX: Only include NON-TEMPORAL features in the agg_map
            for required_col in all_model_features:
                # Ensure only non-temporal, non-target features survive aggregation
                if required_col in df.columns and required_col not in agg_map and required_col not in TEMPORAL_COLS:
                    if df[required_col].dtype == object:
                        agg_map[required_col] = "first" 
                    elif required_col != mapping.target_col:
                        agg_map[required_col] = "mean" 
            
            # Normalize frequency aliases before validation/resample
            freq = normalize_frequency(freq)
            if freq not in normalize_frequency.__defaults__[0] if False else VALID_FREQUENCIES:
                # Accept only normalized set
                if freq not in {"D", "W", "M", "Q", "Y"}:
                    raise ValueError(f"Invalid frequency '{freq}'. Use D/W/M/Q/Y etc.")
            
            # df_agg contains Date Index, Target, and Categoricals/Non-Temporal Features
            df_agg = df.resample(freq).agg(agg_map) 
            
            df_agg[mapping.target_col] = pd.to_numeric(
                df_agg[mapping.target_col], errors="coerce"
            ).astype(np.float64)

            # Insert this just before df_agg_reset = df_agg.reset_index() (around line 437)

            # ... (end of aggregation logic) ...
            
            df_agg[mapping.target_col] = pd.to_numeric(
                df_agg[mapping.target_col], errors="coerce"
            ).astype(np.float64)

            # --- DEBUG CHECKPOINT 1: After Aggregation ---
            print(f"\n--- CHECKPOINT 1: POST-AGGREGATION ---")
            print(f"Model: {model}")
            print(f"Columns (df_agg): {df_agg.columns.tolist()}")
            print("--------------------------------------\n")
            # ----------------------------------------------
            
            # ---- 5. Call the correct model --------------------------------
            df_agg_reset = df_agg.reset_index()

            # ---- 5. Call the correct model --------------------------------
            # df_agg_reset now contains the Date Column and the aggregated data 
            # (ready for prepare_data to extract features from the date column)
            df_agg_reset = df_agg.reset_index()
            
            if model == "prophet_weekly_v1":
                out = predict_prophet(df_agg_reset, mapping, horizon)
            elif model == "xgboost_v1":
                out = predict_xgboost(df_agg_reset, mapping, horizon, model)
            elif model == "lightgbm_model": 
                out = predict_lightgbm(df_agg_reset, mapping, horizon, model)
            elif model == "lstm_v1":
                out = predict_lstm(df_agg_reset, mapping, horizon)
            elif model == "sarima_daily_v1":
                out = predict_sarima(df_agg_reset, mapping, horizon)
            else:
                raise ValueError(f"Model {model} not recognised.")

            # ---- 6. Uniform response --------------------------------------
            results.append(
                PredictionResponseItem(
                    model_name=model, status="success", prediction=out.to_dict("records")
                )
            )
        except Exception as exc:
            print(f"Error: {model} failed with: {exc}")
            results.append(
                PredictionResponseItem(model_name=model, status="error", error=str(exc))
            )
    return results
# --------------------------------------------------------------
# 4. RUNNER
# --------------------------------------------------------------
if __name__ == "__main__":
    # Use PORT from environment (Render) or API_PORT, default to 8000 for local
    port = int(os.getenv("PORT", os.getenv("API_PORT", "8000")))
    uvicorn.run("unified_forecaster_app:app", host="0.0.0.0", port=port, reload=True)