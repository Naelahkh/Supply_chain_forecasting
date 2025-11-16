"""
Feature Engineering Module for Forecasting Models
Handles automatic feature generation for uploaded user data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime

class FeatureEngineer:
    """
    Handles feature engineering for different forecasting models
    """
    
    def __init__(self):
        self.supported_models = [
            'prophet_weekly_v1',
            'xgboost_monthly_cv_v1',
            'lstm_totalrevenue_v1',
            'lstm_v1'
        ]
    
    def engineer_features(
        self, 
        data: pd.DataFrame, 
        model_id: str,
        date_column: str = 'WorkDate'
    ) -> pd.DataFrame:
        """
        Main function to engineer features based on model requirements
        
        Args:
            data: Raw input dataframe
            model_id: ID of the model that will use this data
            date_column: Name of the date column
            
        Returns:
            DataFrame with engineered features
        """
        
        if model_id not in self.supported_models:
            raise ValueError(f"Model {model_id} not supported for feature engineering")
        
        # Make a copy to avoid modifying original
        df = data.copy()
        
        # Convert date column to datetime
        if date_column in df.columns:
            df[date_column] = pd.to_datetime(df[date_column])
        else:
            raise ValueError(f"Date column '{date_column}' not found in data")
        
        # Apply model-specific feature engineering
        if model_id == 'prophet_weekly_v1':
            df = self._engineer_prophet_features(df, date_column)
        
        elif model_id == 'xgboost_monthly_cv_v1':
            df = self._engineer_xgboost_features(df, date_column)
        
        elif model_id in ['lstm_totalrevenue_v1', 'lstm_v1']:
            df = self._engineer_lstm_features(df, date_column)
        
        return df
    
    def _engineer_prophet_features(
        self, 
        df: pd.DataFrame, 
        date_column: str
    ) -> pd.DataFrame:
        """
        Feature engineering for Prophet model
        Prophet expects columns named 'ds' (date) and 'y' (target)
        """
        # Prophet specific transformations
        # Rename columns to Prophet's expected names
        if 'OrderCount' in df.columns:
            df = df.rename(columns={
                date_column: 'ds',
                'OrderCount': 'y'
            })
        
        # Aggregate to weekly if needed
        if 'ds' in df.columns and 'y' in df.columns:
            df['ds'] = pd.to_datetime(df['ds'])
            df = df.groupby(pd.Grouper(key='ds', freq='W')).agg({
                'y': 'sum'
            }).reset_index()
        
        return df
    
    def _engineer_xgboost_features(
        self, 
        df: pd.DataFrame, 
        date_column: str
    ) -> pd.DataFrame:
        """
        Feature engineering for XGBoost model
        """
        # Extract basic date features
        df['year'] = df[date_column].dt.year
        df['month'] = df[date_column].dt.month
        df['quarter'] = df[date_column].dt.quarter
        df['day_of_week'] = df[date_column].dt.dayofweek
        df['day_of_month'] = df[date_column].dt.day
        df['week_of_year'] = df[date_column].dt.isocalendar().week
        
        # Create lag features if we have target column
        if 'OrderCount' in df.columns:
            # Sort by date
            df = df.sort_values(date_column)
            
            # Create lag features (previous values)
            df['lag_1'] = df['OrderCount'].shift(1)
            df['lag_3'] = df['OrderCount'].shift(3)
            df['lag_7'] = df['OrderCount'].shift(7)
            
            # Rolling statistics
            df['roll_mean_7'] = df['OrderCount'].rolling(window=7, min_periods=1).mean()
            df['roll_std_7'] = df['OrderCount'].rolling(window=7, min_periods=1).std()
            df['roll_mean_30'] = df['OrderCount'].rolling(window=30, min_periods=1).mean()
        
        return df
    
    def _engineer_lstm_features(
        self, 
        df: pd.DataFrame, 
        date_column: str
    ) -> pd.DataFrame:
        """
        Feature engineering for LSTM models
        Extracts temporal features that LSTM expects
        """
        # Extract date features
        df['year'] = df[date_column].dt.year
        df['month'] = df[date_column].dt.month
        df['day'] = df[date_column].dt.day
        df['dayofweek'] = df[date_column].dt.dayofweek
        df['quarter'] = df[date_column].dt.quarter
        
        # These are all the features needed for LSTM
        # The date column will be dropped later in the API
        
        return df
    
    def validate_features(
        self, 
        df: pd.DataFrame, 
        model_id: str
    ) -> Dict[str, any]:
        """
        Validate that all required features are present
        
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'missing_features': [],
            'warnings': []
        }
        
        # Define required features for each model
        required_features = {
            'prophet_weekly_v1': ['ds', 'y'],
            'xgboost_monthly_cv_v1': [
                'Customer', 'Location', 'BusinessType', 
                'OrderCount', 'year', 'month', 'quarter'
            ],
            'lstm_totalrevenue_v1': [
                'Customer', 'Location', 'BusinessType', 
                'OrderCount', 'year', 'month', 'day', 'dayofweek', 'quarter'
            ],
            'lstm_v1': [
                'Customer', 'Location', 'BusinessType', 
                'OrderCount', 'year', 'month', 'day', 'dayofweek', 'quarter'
            ]
        }
        
        if model_id in required_features:
            required = required_features[model_id]
            missing = [col for col in required if col not in df.columns]
            
            if missing:
                validation['is_valid'] = False
                validation['missing_features'] = missing
        
        return validation


# ====================================
# STANDALONE FUNCTIONS (For API use)
# ====================================

def prepare_lstm_features(data: pd.DataFrame, date_col: str = 'WorkDate') -> pd.DataFrame:
    """
    Standalone function to prepare features for LSTM models
    
    Args:
        data: Raw input dataframe
        date_col: Name of the date column
        
    Returns:
        DataFrame with engineered features, date column dropped
    """
    df = data.copy()
    
    # Convert to datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Extract features
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['day'] = df[date_col].dt.day
    df['dayofweek'] = df[date_col].dt.dayofweek
    df['quarter'] = df[date_col].dt.quarter
    
    # Save dates for later (if needed for output)
    dates = df[date_col].copy()
    
    # Drop date column (not used in model)
    df = df.drop(date_col, axis=1)
    
    # Reorder columns to expected order
    expected_order = [
        'Customer', 'Location', 'BusinessType', 'OrderCount',
        'year', 'month', 'day', 'dayofweek', 'quarter'
    ]
    
    # Only keep columns that exist
    available_cols = [col for col in expected_order if col in df.columns]
    df = df[available_cols]
    
    return df, dates


def prepare_prophet_features(data: pd.DataFrame, date_col: str = 'WorkDate', target_col: str = 'OrderCount') -> pd.DataFrame:
    """
    Prepare features for Prophet model
    """
    df = data.copy()
    
    # Rename to Prophet's expected column names
    df = df.rename(columns={
        date_col: 'ds',
        target_col: 'y'
    })
    
    df['ds'] = pd.to_datetime(df['ds'])
    
    return df[['ds', 'y']]


def prepare_xgboost_features(data: pd.DataFrame, date_col: str = 'WorkDate') -> pd.DataFrame:
    """
    Prepare features for XGBoost model
    """
    df = data.copy()
    
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Extract features
    df['year'] = df[date_col].dt.year
    df['month'] = df[date_col].dt.month
    df['quarter'] = df[date_col].dt.quarter
    df['day_of_week'] = df[date_col].dt.dayofweek
    
    # Drop date column
    df = df.drop(date_col, axis=1)
    
    return df