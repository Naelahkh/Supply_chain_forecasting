#app_v7.py
import streamlit as st
import pandas as pd
import time
import io
import datetime
import requests
import os
import re
import json
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import plotly.express as px
from pathlib import Path

# --- Imports ---
from rag_engine import get_rag_chain 
from utils.data_validator import validate_dataframe, load_schema 

# Unified forecasting toolkit (local fallback)
from unified_forecaster_app import (
    ColumnMapping as UnifiedColumnMapping,
    predict_prophet as unified_predict_prophet,
    predict_xgboost as unified_predict_xgboost,
    predict_lightgbm as unified_predict_lightgbm,
    predict_lstm as unified_predict_lstm,
    predict_sarima as unified_predict_sarima,
    VALID_FREQUENCIES as UNIFIED_VALID_FREQUENCIES,
    LOADED_MODELS as UNIFIED_MODELS,
)

# --- Analytics Engine Import ---
try:
    from analytics_engine_v2 import DataAnalytics, parse_analytics_request, format_analytics_response
    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    print("Warning: analytics_engine not available") 

# --- API URL (resolve from env for Docker two-container setup) ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_ENDPOINT_URL = f"{BACKEND_URL}/predict"

# --- Load RAG Chain ---
@st.cache_resource
def load_rag_chain_resource():
    """Loads the RAG chain once and caches it."""
    print("Loading RAG chain...")
    chain = get_rag_chain()
    if chain is None:
        print("Error: RAG chain could not be created. Check rag_engine.py logs.")
    else:
        print("RAG chain loaded successfully.")
    return chain

rag_chain = load_rag_chain_resource()

# --- Feature Flags ---
LIGHTGBM_ENABLED = False  # Toggle to disable LightGBM if you need to test other models exclusively

# --- Placeholder Schema (used for clarity in functions) ---
class ForecastPlan(dict):
    """Placeholder for the RAG's structured output plan."""
    model_id: str
    horizon_steps: int
    target_col: str
    regressor_cols: List[str]

# --- 1. Page Configuration ---
if not st.session_state.get("_main_page_config_set", False):
    st.set_page_config(
        page_title="Supply Chain Forecasting Agent",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.session_state["_main_page_config_set"] = True

# Ensure sidebar is visible with CSS and JavaScript
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            transform: translateX(0) !important;
            min-width: 400px !important;
            width: 400px !important;
        }
        section[data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            transform: translateX(0) !important;
            min-width: 400px !important;
            width: 400px !important;
        }
        [data-testid="stSidebar"] > div {
            min-width: 400px !important;
            width: 400px !important;
        }
        [data-testid="stSidebarNav"] {
            display: none !important;
            visibility: hidden !important;
        }
        [data-testid="stSidebar"][aria-expanded="true"] {
            display: block !important;
            visibility: visible !important;
            min-width: 400px !important;
            width: 400px !important;
        }
        [data-testid="stSidebar"][aria-expanded="false"] {
            display: block !important;
            visibility: visible !important;
            min-width: 400px !important;
            width: 400px !important;
        }
        button[data-testid="baseButton-header"][aria-label*="sidebar"],
        button[data-testid="baseButton-header"][aria-label*="menu"] {
            display: block !important;
        }
    </style>
    <script>
        // Force sidebar to be open
        function openSidebar() {
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            const sidebarButton = document.querySelector('button[data-testid="baseButton-header"][aria-label*="sidebar"], button[data-testid="baseButton-header"][aria-label*="menu"]');
            
            if (sidebar) {
                sidebar.style.display = 'block';
                sidebar.style.visibility = 'visible';
                sidebar.style.transform = 'translateX(0)';
                sidebar.setAttribute('aria-expanded', 'true');
            }
            
            if (sidebarButton) {
                sidebarButton.click();
            }
        }
        
        // Run on page load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', openSidebar);
        } else {
            openSidebar();
        }
        
        // Also run after a short delay to ensure Streamlit has rendered
        setTimeout(openSidebar, 100);
        setTimeout(openSidebar, 500);
        setTimeout(openSidebar, 1000);
    </script>
""", unsafe_allow_html=True)

# --- 2. Session State Initialization ---
default_messages = [{"role": "assistant", "content": "Good to see you, I’m Astra, your smart AI assistant , Please Upload user data."}]

if "messages" not in st.session_state: st.session_state.messages = default_messages
if "uploaded_file_df" not in st.session_state: st.session_state.uploaded_file_df = None
if "processed_df" not in st.session_state: st.session_state.processed_df = None
if "data_is_valid" not in st.session_state: st.session_state.data_is_valid = None 
if "validation_warnings" not in st.session_state: st.session_state.validation_warnings = []
if "validation_critical" not in st.session_state: st.session_state.validation_critical = []
if "uploaded_file_obj" not in st.session_state: st.session_state.uploaded_file_obj = None
if "selected_sheet" not in st.session_state: st.session_state.selected_sheet = None
if "rag_analysis" not in st.session_state: st.session_state.rag_analysis = None # Stores the RAG's Step 1 JSON response
if "current_forecast_data" not in st.session_state: st.session_state.current_forecast_data = None
if "column_purposes" not in st.session_state: st.session_state.column_purposes = {}

# --- (Backend Helper Functions) ---

def clear_all_data_states():
    """Resets all session state related to uploaded data and results."""
    st.session_state.uploaded_file_df = None
    st.session_state.processed_df = None
    st.session_state.data_is_valid = None
    st.session_state.validation_warnings = []
    st.session_state.validation_critical = []
    st.session_state.uploaded_file_obj = None
    st.session_state.selected_sheet = None
    st.session_state.rag_analysis = None
    st.session_state.column_purposes = {}
    st.session_state.current_forecast_data = None
    st.session_state.messages = default_messages
    print("Cleared data-related session states.")

def detect_query_intent(query: str, has_data: bool) -> str:
    """
    IMPROVED: More precise intent detection with visualization support
    """
    query_lower = query.lower()
    
    # 1. VISUALIZATION (Check FIRST - most specific)
    viz_keywords = [
        'plot', 'chart', 'visualize', 'graph', 'show chart', 'histogram',
        'scatter', 'bar chart', 'line chart', 'pie chart', 'boxplot',
        'visualization', 'data visualization', 'create visualization',
        'generate visualization'
    ]
    if has_data and any(keyword in query_lower for keyword in viz_keywords):
        return 'visualization'
    
    # 2. ANALYTICS TOOLKIT
    analytics_keywords = {
        'average': ['average', 'mean', 'avg'],
        'basic_stats': ['statistics', 'stats', 'summary', 'describe'],
        'correlation': ['correlation', 'correlate', 'relationship'],
        'outliers': ['outlier', 'anomaly', 'unusual'],
    }
    
    if has_data:
        for analysis_type, keywords in analytics_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                # ADDITIONAL CHECK: Not a forecast query
                if not any(word in query_lower for word in ['forecast', 'predict', 'future', 'next month', 'next week']):
                    return 'analytics_toolkit'
    
    # 3. DATA ANALYSIS (Group by, filter, calculate)
    analysis_keywords = [
        'analyze', 'analysis', 'examine', 'explore',
        'calculate', 'compute', 'find', 'filter',
        'group by', 'group', 'by region', 'by city'
    ]
    
    if has_data and any(keyword in query_lower for keyword in analysis_keywords):
        return 'analytics_toolkit'
    
    # 4. FORECASTING (Check for explicit forecast keywords)
    has_temporal = any(word in query_lower for word in [
        'next', 'future', 'upcoming', 'tomorrow', 'forecast', 'predict'
    ])
    
    has_prediction_word = any(word in query_lower for word in [
        'forecast', 'predict', 'prediction', 'project', 'estimate'
    ])
    
    # Only route to forecast if BOTH conditions met
    if has_temporal and has_prediction_word:
        return 'forecast'
    
    # Explicit forecast commands
    if any(phrase in query_lower for phrase in [
        'run forecast', 'generate forecast', 'do forecast',
        'forecast for', 'forecast using'
    ]):
        return 'forecast'
    
    # Check for horizon specification (e.g., "next 30 days", "6 months")
    if has_data and bool(re.search(r"\d+\s+(month|week|day)s?", query_lower)):
        # If it mentions time periods and has forecast keywords, it's a forecast
        if has_prediction_word:
            return 'forecast'
    
    # 5. GENERAL
    return 'general'

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string for storage"""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode()
    buf.close()
    return img_str

def get_rag_response(prompt: str) -> str:
    """Invokes the RAG chain and returns the text response."""
    if rag_chain is None:
        st.error("RAG system not initialized.")
        return "RAG system unavailable."
    try:
        answer = rag_chain.invoke(prompt)
        return answer if answer and answer.strip() else "No specific answer found in KB."
    except Exception as e:
        print(f"Error invoking RAG chain: {e}")
        st.error(f"Error contacting RAG system: {e}")
        return "Error searching knowledge base."

def _generate_simple_interpretation(
    model_name: str,
    total_forecasted: float,
    results_summary: str,
    patterns: dict
) -> str:
    """Generate simple, concise interpretation"""
    try:
        simple_prompt = (
            f"You are a helpful business analyst. A forecast was just run using the '{model_name}' model. "
            f"The forecast's total predicted value is {total_forecasted:.2f}. "
            f"Here is a statistical summary of the predictions:\n{results_summary}\n\n"
            f"Please provide a CONCISE interpretation (2-3 short paragraphs maximum) that includes:\n"
            f"1. A brief technical explanation (1-2 sentences)\n"
            f"2. Business feedback: key opportunities, risks, and recommended actions (2-3 bullet points)\n"
            f"Keep it brief and actionable. Focus on the most important insights."
        )
        result = get_rag_response(simple_prompt)
        if not result or result.strip() == "":
            return "Simple interpretation unavailable. Please try the Enhanced view."
        return result
    except Exception as e:
        print(f"Error generating simple interpretation: {e}")
        return f"Error generating simple interpretation: {str(e)}"

def _generate_enhanced_interpretation(
    model_name: str,
    total_forecasted: float,
    results_summary: str,
    patterns: dict,
    forecast_values: list
) -> str:
    """Generate enhanced, business-friendly interpretation"""
    try:
        enhanced_prompt = (
            f"You are a Senior Business Forecasting Consultant with 15+ years of experience. "
            f"Translate these technical forecast results into boardroom-ready strategic insights for C-suite executives.\n\n"
            f"FORECAST SUMMARY:\n"
            f"- Forecast Horizon: {len(forecast_values)} periods\n"
            f"- Total Forecasted Value: {total_forecasted:,.2f}\n"
            f"- Average per Period: {patterns.get('mean', 0):.2f}\n"
            f"- Range: {patterns.get('min', 0):.2f} to {patterns.get('max', 0):.2f}\n"
            f"- Trend: {patterns.get('trend_description', 'stable')}\n"
            f"- Volatility: {patterns.get('volatility', 'moderate')} (Variation: {patterns.get('coefficient_of_variation', 0):.1f}%)\n\n"
            f"Statistical Details:\n{results_summary}\n\n"
            f"CRITICAL REQUIREMENTS:\n"
            f"1. NEVER mention technical model names (Prophet/LSTM/XGBoost) - use 'pattern recognition system', 'forecasting engine', or 'advanced analytics'\n"
            f"2. Use business terminology only (NO technical metrics like RMSE, MAE)\n"
            f"3. Quantify everything with specific numbers, percentages, or units\n"
            f"4. Convert 'confidence intervals' to 'reliability ranges' or 'expected outcome bands'\n"
            f"5. Use terms like 'market instability' instead of 'volatility', 'key drivers' instead of 'features'\n\n"
            f"Provide a CONCISE interpretation (2-3 short paragraphs) covering:\n"
            f"1. Executive Summary: What the forecast shows and its business implication (2-3 sentences)\n"
            f"2. Key Insights: Main patterns, trends, and what they mean for business planning (2-3 sentences)\n"
            f"3. Business Recommendations: Concrete actionable steps (2-3 bullet points)\n\n"
            f"Write in professional but accessible tone. Focus on actionable insights that executives can use immediately."
        )
        result = get_rag_response(enhanced_prompt)
        if not result or result.strip() == "":
            return "Enhanced interpretation unavailable. Please try the Simple view."
        return result
    except Exception as e:
        print(f"Error generating enhanced interpretation: {e}")
        return f"Error generating enhanced interpretation: {str(e)}"

def _analyze_forecast_patterns(forecast_values: list) -> dict:
    """Analyze statistical patterns in forecast values"""
    if not forecast_values or len(forecast_values) == 0:
        return {}
    
    import numpy as np
    values = np.array(forecast_values)
    
    # Basic statistics
    mean_val = float(np.mean(values))
    std_val = float(np.std(values))
    min_val = float(np.min(values))
    max_val = float(np.max(values))
    
    # Trend analysis
    if len(values) > 1:
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        trend_change = ((np.mean(second_half) - np.mean(first_half)) / np.mean(first_half)) * 100 if np.mean(first_half) > 0 else 0
        
        if trend_change > 5:
            trend = "increasing"
            trend_desc = f"upward trend of {trend_change:.1f}%"
        elif trend_change < -5:
            trend = "decreasing"
            trend_desc = f"downward trend of {abs(trend_change):.1f}%"
        else:
            trend = "stable"
            trend_desc = "relatively stable pattern"
    else:
        trend = "stable"
        trend_desc = "insufficient data for trend analysis"
        trend_change = 0.0
    
    # Volatility
    cv = (std_val / mean_val) * 100 if mean_val > 0 else 0
    if cv < 10:
        volatility = "low"
    elif cv < 25:
        volatility = "moderate"
    else:
        volatility = "high"
    
    return {
        'mean': mean_val,
        'std': std_val,
        'min': min_val,
        'max': max_val,
        'range': float(max_val - min_val),
        'trend': trend,
        'trend_change_pct': float(trend_change),
        'trend_description': trend_desc,
        'volatility': volatility,
        'coefficient_of_variation': float(cv)
    }

def extract_json_from_response(text: str) -> dict | None:
    """Finds and parses the first valid JSON object in a string."""
    match = re.search(r"```json\n([\s\S]*?)\n```", text)
    if not match:
        match = re.search(r"({[\s\S]*})", text)
    
    if match:
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSONDecodeError: {e} in string: {json_str}")
            return None
    return None

def call_forecast_api(post_data: dict) -> dict | None:
    """Sends the forecast request to FastAPI and handles the response."""
    with st.status("Agent processing forecast...", expanded=True) as status:
        try:
            status.write(f"Contacting API: {API_ENDPOINT_URL}...")
            response = requests.post(API_ENDPOINT_URL, json=post_data, timeout=300)
            response.raise_for_status()
            
            status.write("Receiving forecast data...")
            
            response_list = response.json()
            if not isinstance(response_list, list) or len(response_list) == 0:
                raise Exception(f"API returned an unexpected response: {response_list}")
            
            forecast_data = response_list[0]
            
            if forecast_data.get("status") == "error":
                # CRITICAL: Print the exact API error reported in the logs
                error_msg = forecast_data.get('error', 'Unknown')
                print(f"API Execution Error: {error_msg}") 
                raise RuntimeError(f"Prediction Error: {error_msg}")
            
            if not forecast_data.get("prediction"):
                raise Exception("API returned success but no 'prediction' data.")

            forecast_df_api = pd.DataFrame(forecast_data["prediction"]) # Renamed variable

            # CRITICAL FIX: The FastAPI backend standardizes output to 'date' and 'prediction'
            date_col = 'date' 
            pred_col = 'prediction'
            
            if date_col not in forecast_df_api.columns or pred_col not in forecast_df_api.columns:
                raise Exception("API output missing standard date or prediction columns.")
                
            forecast_df_api[date_col] = pd.to_datetime(forecast_df_api[date_col])

            status.write("Generating interpretation...")
            
            # --- RAG EXPLAINS THE RESULTS ---
            results_summary = forecast_df_api[[pred_col]].describe().to_string()
            model_name = forecast_data.get("model_name", "the selected model")
            total_forecasted_value = forecast_df_api[pred_col].sum()
            forecast_values = forecast_df_api[pred_col].tolist()
            
            # Analyze patterns
            patterns = _analyze_forecast_patterns(forecast_values)
            
            # Generate both interpretations (user will choose which to display)
            status.write("Generating simple interpretation...")
            simple_interpretation = _generate_simple_interpretation(
                model_name, total_forecasted_value, results_summary, patterns
            )
            
            status.write("Generating enhanced interpretation...")
            enhanced_interpretation = _generate_enhanced_interpretation(
                model_name, total_forecasted_value, results_summary, patterns, forecast_values
            )
            
            # Verify both were generated
            if not simple_interpretation or simple_interpretation.strip() == "":
                print("Warning: Simple interpretation is empty")
            if not enhanced_interpretation or enhanced_interpretation.strip() == "":
                print("Warning: Enhanced interpretation is empty")
            
            # Store both interpretations (default to enhanced)
            interpretation = enhanced_interpretation if enhanced_interpretation else simple_interpretation
            # --- END OF RAG STEP ---

            total_forecasted = forecast_df_api[pred_col].sum()
            
            # NOTE: We define forecast_df_api here so it can be used for the KPIs/plot
            # But we must pass its data, not the DF object itself.
            results = {
                "kpi_1_value": f"{total_forecasted:,.0f}",
                "kpi_1_delta": "",
                "kpi_2_value": "N/A",
                "kpi_2_delta": "",
                "kpi_3_value": model_name,
                "forecast_plot_data": forecast_df_api.to_dict('list'),
                "forecast_df_data": forecast_df_api.to_dict('list'),
                "interpretation": interpretation,
                "interpretation_simple": simple_interpretation,
                "interpretation_enhanced": enhanced_interpretation,
                # Store date and prediction column names for robust display
                "date_col_name": date_col, 
                "pred_col_name": pred_col,
                "horizon_steps_value": post_data["items"][0]["horizon_steps"]
            }
            
            status.update(label="Forecast complete!", state="complete")
            return results
            
        except requests.exceptions.HTTPError as http_err:
            status.update(label=f"HTTP Error: {http_err}", state="error")
            st.error(f"HTTP Error: {http_err} - Check FastAPI server logs.")
            raise RuntimeError(str(http_err)) from http_err
        except requests.exceptions.ConnectionError as conn_err:
            status.update(label=f"Connection Error: {conn_err}", state="error")
            st.error("Connection Error: FastAPI server is not running or URL is incorrect.")
            raise RuntimeError(str(conn_err)) from conn_err
        except Exception as e:
            print(f"Error during API call: {e}")
            st.error(f"Error during API call: {e}")
            status.update(label=f"Error: {e}", state="error")
            raise RuntimeError(str(e)) from e


def run_local_lightgbm_forecast(
    df_source: pd.DataFrame,
    mapping_info: Dict[str, Any],
    horizon: int,
    frequency: str,
) -> Dict[str, Any]:
    """Fallback LightGBM forecast using the unified forecasting toolkit."""
    if df_source is None or df_source.empty:
        raise ValueError("No data available for local forecasting fallback.")

    mapping_obj = UnifiedColumnMapping(
        date_col=mapping_info["date_col"],
        target_col=mapping_info["target_col"],
        regressor_cols=mapping_info.get("regressor_cols") or [],
    )

    df_local = df_source.copy()

    # Ensure required columns exist with safe defaults
    categorical_defaults = {"customer", "location", "businesstype"}
    for reg in mapping_obj.regressor_cols or []:
        reg_lower = reg.lower()
        if reg not in df_local.columns:
            if reg_lower in categorical_defaults:
                df_local[reg] = "Unknown"
            else:
                df_local[reg] = 0
        else:
            if reg_lower in categorical_defaults:
                df_local[reg] = df_local[reg].astype(str).replace({"nan": "Unknown"})

    # Clean target/date columns
    df_local[mapping_obj.target_col] = (
        df_local[mapping_obj.target_col]
        .astype(str)
        .str.replace(r"[^\d.]", "", regex=True)
    )
    df_local[mapping_obj.target_col] = pd.to_numeric(
        df_local[mapping_obj.target_col], errors="coerce"
    )
    df_local[mapping_obj.date_col] = pd.to_datetime(
        df_local[mapping_obj.date_col], errors="coerce"
    )

    df_local = df_local.dropna(subset=[mapping_obj.date_col, mapping_obj.target_col])
    if df_local.empty:
        raise ValueError("Cleaned dataset is empty after preprocessing.")

    df_local = df_local.set_index(mapping_obj.date_col).sort_index()

    freq_local = (frequency or "D").upper()
    if freq_local == "M":
        freq_local = "ME"
    if freq_local not in UNIFIED_VALID_FREQUENCIES:
        raise ValueError(f"Unsupported frequency '{frequency}' for local forecast.")

    agg_map = {mapping_obj.target_col: "sum"}
    for reg in mapping_obj.regressor_cols or []:
        if reg in df_local.columns:
            if pd.api.types.is_numeric_dtype(df_local[reg]):
                agg_map[reg] = "mean"
            else:
                agg_map[reg] = "first"

    df_agg = df_local.resample(freq_local).agg(agg_map)
    df_agg[mapping_obj.target_col] = pd.to_numeric(
        df_agg[mapping_obj.target_col], errors="coerce"
    ).astype(float)

    df_agg_reset = df_agg.reset_index()

    predictions_df = unified_predict_lightgbm(
        df_agg_reset, mapping_obj, horizon, "lightgbm_model"
    )

    if predictions_df.empty:
        raise ValueError("Local LightGBM forecasting returned no results.")

    # Ensure datetime for plotting and summary
    predictions_df["date"] = pd.to_datetime(predictions_df["date"], errors="coerce")

    total_forecasted = predictions_df["prediction"].sum()
    results_summary = predictions_df[["prediction"]].describe().to_string()
    model_name = "lightgbm_model"

    # Analyze patterns
    forecast_values_list = predictions_df["prediction"].tolist()
    patterns = _analyze_forecast_patterns(forecast_values_list)
    
    # Generate both interpretations (user will choose which to display)
    simple_interpretation = _generate_simple_interpretation(
        model_name, total_forecasted, results_summary, patterns
    )
    enhanced_interpretation = _generate_enhanced_interpretation(
        model_name, total_forecasted, results_summary, patterns, forecast_values_list
    )
    
    # Verify both were generated
    if not simple_interpretation or simple_interpretation.strip() == "":
        print("Warning: Simple interpretation is empty")
    if not enhanced_interpretation or enhanced_interpretation.strip() == "":
        print("Warning: Enhanced interpretation is empty")
    
    # Store both interpretations (default to enhanced)
    interpretation = enhanced_interpretation if enhanced_interpretation else simple_interpretation

    forecast_plot_df = predictions_df.copy()
    forecast_plot_df_serializable = forecast_plot_df.copy()
    forecast_plot_df_serializable["date"] = forecast_plot_df_serializable["date"].astype(
        str
    )

    forecast_df_serializable = predictions_df.copy()
    forecast_df_serializable["date"] = forecast_df_serializable["date"].astype(str)

    return {
        "kpi_1_value": f"{total_forecasted:,.0f}",
        "kpi_1_delta": "",
        "kpi_2_value": "N/A",
        "kpi_2_delta": "",
        "kpi_3_value": model_name,
        "forecast_plot_data": forecast_plot_df_serializable.to_dict("list"),
        "forecast_df_data": forecast_df_serializable.to_dict("list"),
        "interpretation": interpretation,
        "interpretation_simple": simple_interpretation,
        "interpretation_enhanced": enhanced_interpretation,
        "date_col_name": "date",
        "pred_col_name": "prediction",
        "horizon_steps_value": horizon,
    }


def run_rag_analysis_step_1(df_raw: pd.DataFrame):
    """Initial RAG analysis to identify core columns and initial model recommendation."""
    st.write("Asking RAG for initial column roles...")
    df_head_str = df_raw.head().to_csv(index=False)
    column_list = df_raw.columns.tolist()

    available_models_list = [
        "'prophet_weekly_v1'",
        "'lstm_v1'",
        "'xgboost_v1'",
        "'sarima_daily_v1'"
    ]
    if LIGHTGBM_ENABLED:
        available_models_list.insert(2, "'lightgbm_model'")

    analysis_prompt = f"""
You are an expert data analyst and recommender. A user uploaded a file with these columns: {column_list}.
Here are the first 5 rows (in CSV format):
{df_head_str}

The available models are: [{', '.join(available_models_list)}].
Based *only* on the data structure and column names:
1. Identify the 'date_col' (the main date or timestamp).
2. Identify the 'target_col' (the main numerical value to be forecasted).
3. Identify a list of all other suitable columns to use as 'regressor_cols' (additional features).
Please respond with *only* a single JSON object in a ```json code block with these keys.
Example response:
```json
{{
  "date_col": "Order_Date",
  "target_col": "Sales_Qty",
  "regressor_cols": ["Store_ID", "Promotion_Flag"]
}}
```
"""
    rag_text_response = get_rag_response(analysis_prompt)
    rag_json = extract_json_from_response(rag_text_response)
    return rag_json, rag_text_response

def run_rag_analysis_step_2(df_raw: pd.DataFrame, chat_prompt: str, initial_analysis: dict) -> dict:
    """Final RAG analysis to select model and horizon based on user's query."""
    
    initial_analysis_str = json.dumps(initial_analysis)
    
    available_models_step2 = [
        "'prophet_weekly_v1'",
        "'lstm_v1'",
        "'xgboost_v1'",
        "'sarima_daily_v1'"
    ]
    decision_tree_instructions = """
STEP 1: Check data frequency and categorical features:
- If data is MONTHLY (frequency='M' or 'ME') AND has Customer/Location/BusinessType columns → USE 'xgboost_v1'
- If data is WEEKLY (frequency='W') → USE 'prophet_weekly_v1'
- If data is DAILY → Use 'lstm_v1' or 'sarima_daily_v1' depending on seasonality and user preference.

STEP 2: Model-specific details:
- 'xgboost_v1': MONTHLY data with Customer/Location/BusinessType. Has lag features (1, 3, 6 months) and rolling statistics (3, 6, 12 months). Target: NumberOfPieces.
- 'lstm_v1': DAILY data WITHOUT categorical features OR user explicitly requests deep learning/neural network. Uses sequence learning.
- 'sarima_daily_v1': DAILY univariate time series with weekly seasonality. NO categorical features needed.
- 'prophet_weekly_v1': WEEKLY data with strong seasonality patterns.
"""

    if LIGHTGBM_ENABLED:
        available_models_step2.insert(2, "'lightgbm_model'")
        decision_tree_instructions = """
STEP 1: Check data frequency and categorical features:
- If data is DAILY (frequency='D') AND has Customer/Location/BusinessType columns → USE 'lightgbm_model'
- If data is MONTHLY (frequency='M' or 'ME') AND has Customer/Location/BusinessType columns → USE 'xgboost_v1'
- If data is WEEKLY (frequency='W') → USE 'prophet_weekly_v1'
- If data is DAILY but NO Customer/Location/BusinessType columns → USE 'lstm_v1' or 'sarima_daily_v1'

STEP 2: Model-specific details:
- 'lightgbm_model': DAILY data with Customer/Location/BusinessType. Has lag features (1, 7, 14 days) and rolling statistics (7, 14 days). Handles OrderCount and NumberOfPieces. Target: TotalRevenue.
- 'xgboost_v1': MONTHLY data with Customer/Location/BusinessType. Has lag features (1, 3, 6 months) and rolling statistics (3, 6, 12 months). Target: NumberOfPieces.
- 'lstm_v1': DAILY data WITHOUT categorical features OR user explicitly requests deep learning/neural network. Uses sequence learning.
- 'sarima_daily_v1': DAILY univariate time series with weekly seasonality. NO categorical features needed.
- 'prophet_weekly_v1': WEEKLY data with strong seasonality patterns.

CRITICAL PRIORITY RULES:
1. DAILY + Customer/Location/BusinessType columns → ALWAYS choose 'lightgbm_model' (NOT LSTM, NOT XGBoost)
2. MONTHLY + Customer/Location/BusinessType columns → ALWAYS choose 'xgboost_v1' (NOT LightGBM)
3. DAILY + NO categorical features → Choose 'lstm_v1' or 'sarima_daily_v1'
4. WEEKLY data → Choose 'prophet_weekly_v1'
"""
    else:
        decision_tree_instructions += """

CRITICAL PRIORITY RULES:
1. MONTHLY + Customer/Location/BusinessType columns → ALWAYS choose 'xgboost_v1'
2. DAILY + NO categorical features → Choose 'lstm_v1' or 'sarima_daily_v1'
3. WEEKLY data → Choose 'prophet_weekly_v1'
"""

    final_prompt = f"""
TASK: AUTOMATED FORECAST PLAN GENERATION
User's explicit request must be followed to finalize the parameters.

USER'S QUERY: "{chat_prompt}"
UPLOADED DATA ANALYSIS: {initial_analysis_str}
AVAILABLE MODELS: [{', '.join(available_models_step2)}]

MODEL SELECTION DECISION TREE (FOLLOW IN ORDER):
{decision_tree_instructions}

Instructions:
1. FIRST check the data frequency (D/M/W) and presence of Customer/Location/BusinessType columns from UPLOADED DATA ANALYSIS
2. Apply the decision tree above to select 'model_id' - FOLLOW THE PRIORITY RULES STRICTLY
3. Determine the forecast 'horizon_steps' (the number of periods to predict, e.g., 30 days, 6 months, 12 weeks)
4. Set 'frequency' based on data frequency (D for daily, M/ME for monthly, W for weekly)
5. Confirm or refine the 'target_col' and 'regressor_cols' based on the user's specific mention in the query

Provide ONLY the JSON object. DO NOT include any conversational text, rationale, or preamble.

```json
{{
  "model_id": "...",
  "horizon_steps": <int>,
  "target_col": "...",
  "regressor_cols": [...],
  "frequency": "..." 
}}
```
"""

    st.write("Asking RAG for final model selection and forecast parameters...")
    rag_json = None
    rag_text_response = get_rag_response(final_prompt)

    rag_json = extract_json_from_response(rag_text_response) 

    if rag_json is None:
        try:
            # Fallback for plain JSON string output
            rag_json = json.loads(rag_text_response.strip())
        except Exception:
            st.error(f"RAG failed to produce valid JSON. Full response: {rag_text_response}")
            return None
    
    return rag_json

# --- 3. Sidebar (Control Panel) ---
# Get the base directory for file paths
BASE_DIR = Path(__file__).parent
LOGO_PATH = BASE_DIR / "images" / "logo2.png"

with st.sidebar:
    st.title("Forecasting Agent")
    if LOGO_PATH.exists(): 
        st.image(str(LOGO_PATH))
    st.markdown("---")

    st.title("🤖 Welcome to InsightFlow AI ✨")
    st.caption("Google RAG: Forecasting & Analysis")
    
    st.markdown("---")
    st.subheader("LLM Models")
    
    # Google RAG for Forecasting and Analysis
    st.markdown("**🔮 Forecasting & Analysis:**")
    if rag_chain:
        st.markdown("✅ Google Gemini RAG")
    else:
        st.markdown("⚠️ Google RAG Unavailable")
    
    # Analytics Toolkit Status
    st.markdown("**📊 Analytics Toolkit:**")
    if ANALYTICS_AVAILABLE:
        st.markdown("✅ Available")
    else:
        st.markdown("⚠️ Unavailable")
    
    # API Status
    st.markdown("---")
    st.subheader("API Status")
    
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
    if GOOGLE_API_KEY:
        st.success("✅ Google API Ready")
    else:
        st.error("❌ Google API Missing")
    
    st.markdown("---")
    st.header("1. Upload Data")
    uploaded_file = st.file_uploader("Upload CSV/Excel file", type=["csv", "xlsx"], key="sidebar_file_uploader_widget")

    sheet_names = []
    show_sheet_selector = False
    
    if uploaded_file is not None:
        if st.session_state.uploaded_file_obj is None or uploaded_file.name != st.session_state.uploaded_file_obj.name:
            clear_all_data_states()
            st.session_state.uploaded_file_obj = uploaded_file
        
        if uploaded_file.name.endswith('.xlsx'):
            show_sheet_selector = True
            try:
                xls = pd.ExcelFile(uploaded_file)
                sheet_names = xls.sheet_names
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")
                clear_all_data_states()
                st.rerun()

    if show_sheet_selector:
        st.session_state.selected_sheet = st.selectbox(
            "Please select the data sheet:",
            options=sheet_names,
            key="sheet_selector"
        )

    load_ready = (uploaded_file is not None) and \
                 (not uploaded_file.name.endswith('.xlsx') or st.session_state.selected_sheet is not None)

    # --- "Process Data" Button (Initial RAG Analysis & Validation) ---
    if load_ready and st.session_state.rag_analysis is None:
        if st.button("Process & Analyze Data", type="primary"):
            try:
                with st.spinner("Loading and running initial RAG analysis..."):
                    if uploaded_file.name.endswith('.csv'):
                        df_raw = pd.read_csv(uploaded_file, low_memory=False)
                    else:
                        df_raw = pd.read_excel(uploaded_file, engine='openpyxl', sheet_name=st.session_state.selected_sheet)
                    
                    st.session_state.uploaded_file_df = df_raw.copy()
                    
                    # --- STEP 1: RAG IDENTIFIES COLUMNS & FEATURES ---
                    rag_json, rag_text = run_rag_analysis_step_1(df_raw)

                    if rag_json and all(k in rag_json for k in ["date_col", "target_col", "regressor_cols"]):
                        st.session_state.rag_analysis = rag_json
                        
                        # Set column_purposes for analytics engine
                        st.session_state.column_purposes = {
                            rag_json['date_col']: 'time_index',
                            rag_json['target_col']: 'target_value'
                        }
                        
                        # --- VALIDATE BASED ON RAG's RESPONSE ---
                        # We only pass the two main columns to the general validator
                        validation_map = {
                            'time_index': rag_json['date_col'],
                            'target_value': rag_json['target_col'],
                        }
                        
                        schema = load_schema("supply_chain_schema")
                        is_valid, df_processed, warnings, critical = validate_dataframe(df_raw.copy(), schema, validation_map)
                        
                        st.session_state.data_is_valid = is_valid
                        st.session_state.validation_warnings = warnings
                        st.session_state.validation_critical = critical
                        
                        if not critical:
                            st.session_state.processed_df = df_processed
                            st.success("Data Uploader Successfully How can I help you explore your data today.")
                            st.session_state.messages.append({"role": "assistant", 
                                "content": f"Data analysis confirmed: Date column: **{rag_json['date_col']}**, Target column: **{rag_json['target_col']}**."})
                        else:
                            st.error("Critical issue found. Cannot proceed.")
                    else:
                        st.error(f"RAG analysis failed: Could not parse required JSON from: {rag_text}")
                        st.session_state.rag_analysis = None
                
            except Exception as e:
                st.error(f"Error loading file: {e}")
                clear_all_data_states()
            
            st.rerun()

    # --- Display Validation Status (CLEANED) ---
    if st.session_state.uploaded_file_df is not None:
        st.markdown("---")
        st.subheader("Data Status")
        if st.session_state.validation_critical:
            st.error("CRITICAL ISSUE: Cannot proceed.")
        elif st.session_state.data_is_valid == True and st.session_state.rag_analysis:
            if st.session_state.validation_warnings:
                # Concise warning message, directing user to Data Explorer
                st.warning("Data Ready, but Warnings Found. See Data Explorer tab for details.") 
            else:
                st.success("Data Ready ✅ (No Warnings)")
            st.json(st.session_state.rag_analysis)
        elif st.session_state.rag_analysis is None:
            st.info("Pending: Click 'Process & Analyze Data'")

        if st.button("Clear Uploaded Data", type="secondary"):
            clear_all_data_states()
            st.rerun()

    # --- Chat Controls ---
    st.markdown("---")
    st.header("2. Chat Controls")
    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = default_messages
        st.rerun()


# Top-level chat input (must NOT be inside tabs/columns/expander/forms/sidebar)
_global_prompt = st.chat_input("Ask about data or request a forecast...", key="main_chat_input")
if _global_prompt:
    st.session_state["_incoming_prompt"] = _global_prompt

# Split the workspace into two permanent tabs: Chat and Dashboard
tab_chat, tab_dashboard, tab_explorer = st.tabs([
    "💬 Agent Chat", 
    "📊 Forecast Dashboard", 
    "📁 Data Explorer"
])

with tab_chat:
    st.header("InsightFlow Chat")
    st.caption("📊 Google RAG handles forecasting & analysis | 🔮 Analytics toolkit for quick insights")
    
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg.get("content", ""))

            # Handle visualization results
            if "visualization" in msg:
                if isinstance(msg["visualization"], str):
                    # Base64 encoded image
                    try:
                        image_data = base64.b64decode(msg["visualization"])
                        st.image(image_data, use_column_width=True)
                    except:
                        st.error("Could not display visualization")
                elif isinstance(msg["visualization"], (plt.Figure, plt.Axes)):
                    st.pyplot(msg["visualization"])
                else:
                    st.plotly_chart(msg["visualization"], width="stretch")
            
            # Handle forecast previews
            if "forecast_preview" in msg:
                preview = msg["forecast_preview"]
                forecast_df = pd.DataFrame(preview.get("forecast_df", {}))
                date_col = preview.get("date_col", "date")
                pred_col = preview.get("pred_col", "prediction")
                
                # Get both interpretations from preview
                interpretation_enhanced = preview.get("interpretation_enhanced", "")
                interpretation_simple = preview.get("interpretation_simple", "")
                
                # Business Insights View Selector for chat history
                if interpretation_enhanced or interpretation_simple:
                    st.markdown("---")
                    st.markdown("### 💼 Business Insights View")
                    
                    has_both = bool(interpretation_enhanced) and bool(interpretation_simple)
                    
                    if has_both:
                        # Show radio buttons with Simple as default
                        insight_style = st.radio(
                            "Choose your business insights view:",
                            ["Simple & Direct", "Enhanced Business View"],
                            index=0,  # Default to Simple
                            key=f"chat_history_insight_{hash(str(msg.get('content', '')))}",
                            horizontal=True
                        )
                        
                        if insight_style == "Enhanced Business View":
                            selected_interpretation = interpretation_enhanced
                            style_badge = "💼 **Enhanced Business View**"
                        else:
                            selected_interpretation = interpretation_simple
                            style_badge = "📝 **Simple & Direct**"
                        
                        st.markdown(style_badge)
                        st.markdown("---")
                        st.markdown(selected_interpretation)
                        
                        # Show info about the selected style
                        if insight_style == "Enhanced Business View":
                            st.info("💡 **Enhanced View:** Executive-friendly language with detailed pattern analysis, trends, and business recommendations.")
                        else:
                            st.info("💡 **Simple View:** Quick, concise summary with essential insights and recommendations.")
                    else:
                        # Only one available - show it
                        if interpretation_simple:
                            st.markdown("📝 **Simple & Direct**")
                            st.markdown("---")
                            st.markdown(interpretation_simple)
                        elif interpretation_enhanced:
                            st.markdown("💼 **Enhanced Business View**")
                            st.markdown("---")
                            st.markdown(interpretation_enhanced)
                        elif preview.get("interpretation"):
                            # Fallback to default interpretation
                            st.markdown("**Interpretation:**")
                            st.markdown("---")
                            st.markdown(preview.get("interpretation", ""))
                
                if not forecast_df.empty and date_col in forecast_df.columns and pred_col in forecast_df.columns:
                    # Ensure date column is datetime for proper chart display
                    try:
                        if not pd.api.types.is_datetime64_any_dtype(forecast_df[date_col]):
                            forecast_df[date_col] = pd.to_datetime(forecast_df[date_col])
                    except:
                        pass  # If conversion fails, continue anyway
                    
                    plot_cols = [date_col, pred_col]
                    for col in ['yhat_lower', 'yhat_upper', 'target_value']:
                        if col in forecast_df.columns:
                            plot_cols.append(col)
                    
                    plot_cols = [col for col in plot_cols if col in forecast_df.columns]
                    if len(plot_cols) >= 2:
                        st.line_chart(forecast_df[plot_cols], x=date_col)
                        
                        # Show first few rows in expander
                        with st.expander("📊 View Forecast Data (First 10 rows)"):
                            display_cols = [date_col, pred_col]
                            if 'yhat_lower' in forecast_df.columns:
                                display_cols.append('yhat_lower')
                            if 'yhat_upper' in forecast_df.columns:
                                display_cols.append('yhat_upper')
                            st.dataframe(forecast_df[display_cols].head(10))
   
    # Consume top-level prompt inside the chat tab
    prompt = st.session_state.pop("_incoming_prompt", None)
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            has_data = st.session_state.processed_df is not None
            intent = detect_query_intent(prompt, has_data)
            
            st.caption(f"🎯 Routing to: {intent.replace('_', ' ').title()}")
            
            # Route 1: Analytics Toolkit (Fast, local)
            if intent == 'analytics_toolkit' and ANALYTICS_AVAILABLE:
                with st.spinner("Running analytics..."):
                    result = parse_analytics_request(
                        prompt,
                        st.session_state.processed_df,
                        st.session_state.column_purposes
                    )
                    analysis_type, results = result
                    if analysis_type == 'visualization':
                        if results.get('success', False):
                            if 'image' in results:
                                try:
                                    image_data = base64.b64decode(results['image'])
                                    st.image(image_data, use_column_width=True)
                                    caption = f"📊 {results.get('chart_type', 'Visualization')}"
                                    st.caption(caption)
                                    if results.get('columns'):
                                        st.caption(f"Columns: {', '.join(results['columns'])}")
                                    if results.get('explanation'):
                                        st.markdown(f"**Explanation:** {results['explanation']}")
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": caption,
                                        "visualization": results['image']
                                    })
                                except Exception as viz_err:
                                    error_msg = f"📊 Error displaying visualization: {viz_err}"
                                    st.error(error_msg)
                                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                            else:
                                error_msg = "📊 Visualization generated but no image data returned."
                                st.error(error_msg)
                                st.session_state.messages.append({"role": "assistant", "content": error_msg})
                        else:
                            error_msg = results.get('error', 'Unknown error')
                            suggestion = ""
                            if st.session_state.processed_df is not None:
                                available_cols = st.session_state.processed_df.columns.tolist()
                                if available_cols:
                                    suggestion = f"\n\n💡 Try specifying columns like: {', '.join(available_cols[:3])}"
                            response = f"📊 Error generating visualization: {error_msg}{suggestion}"
                            st.error(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                    else:
                        formatted = format_analytics_response(analysis_type, results)
                        response = f"✅ **Analytics** ({analysis_type})\n\n{formatted}"
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Route 2: Forecasting (Google RAG)
            elif intent == 'forecast':
                # --- Run Forecast Intent ---
                
                # 1. Check data status
                if st.session_state.validation_critical:
                    assistant_response = "Cannot proceed. Please fix the critical issues in the sidebar first."
                    st.markdown(assistant_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                elif st.session_state.rag_analysis is None or st.session_state.processed_df is None:
                    assistant_response = "Please upload and click 'Process & Analyze Data' in the sidebar first."
                    st.markdown(assistant_response)
                    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                else:
                    # 2. STEP 2: RAG performs final selection based on QUERY
                    initial_analysis = st.session_state.rag_analysis
                    try:
                        final_analysis = run_rag_analysis_step_2(st.session_state.processed_df, prompt, initial_analysis)
                        
                        if final_analysis and all(k in final_analysis for k in ["model_id", "horizon_steps", "target_col", "frequency"]):
                            
                            model_id_to_use = final_analysis['model_id']
                            
                            # 3. Build the ColumnMapping for the API
                            api_mapping = {
                                "date_col": initial_analysis['date_col'], 
                                "target_col": final_analysis.get('target_col', initial_analysis['target_col']),
                                "regressor_cols": final_analysis.get('regressor_cols', initial_analysis.get('regressor_cols', []))
                            }
                            
                            # Keep a clean copy for potential local fallback
                            df_for_local = st.session_state.processed_df.copy()

                            # 4. Prepare data for JSON serialization
                            data_df_copy = df_for_local.copy()
                            date_col_name = initial_analysis['date_col']
                            
                            # FIX 1: Convert datetime to string
                            if date_col_name in data_df_copy.columns:
                                data_df_copy[date_col_name] = data_df_copy[date_col_name].astype(str)
                            
                            # FIX 2: Replace all NaNs with None
                            data_df_json_safe = data_df_copy.where(pd.notnull(data_df_copy), None)

                            data_to_send = data_df_json_safe.to_dict('records')

                            # 5. Build the final post_data
                            post_data = {
                                "items": [
                                    {
                                        "model_name": model_id_to_use,
                                        "column_mapping": api_mapping,
                                        "data": data_to_send,
                                        "horizon_steps": final_analysis['horizon_steps'],
                                        "frequency": final_analysis['frequency']
                                    }
                                ]
                            }
                            
                            assistant_response = f"Understood! Running a {final_analysis['horizon_steps']} step forecast with model `{model_id_to_use}`..."
                            st.markdown(assistant_response)

                            # 6. Call the API with local fallback if needed
                            if model_id_to_use == "lightgbm_model":
                                if not LIGHTGBM_ENABLED:
                                    st.error("LightGBM model is currently disabled for testing. Please adjust your query or re-enable LightGBM.")
                                    results = None
                                else:
                                    try:
                                        results = run_local_lightgbm_forecast(
                                            df_for_local,
                                            api_mapping,
                                            final_analysis['horizon_steps'],
                                            final_analysis['frequency'],
                                        )
                                        st.success("Local LightGBM forecast completed successfully.")
                                    except Exception as local_err:
                                        st.error(f"Local LightGBM forecast failed: {local_err}")
                                        results = None
                            else:
                                try:
                                    results = call_forecast_api(post_data)
                                except RuntimeError as api_error:
                                    results = None
                                    error_message = str(api_error)
                                    st.warning(f"API forecast error: {error_message}")

                                    st.error("No local fallback available for this model.")
                            
                            if results:
                                try:
                                    st.session_state.current_forecast_data = {
                                        **results,
                                        "horizon_steps_value": final_analysis['horizon_steps']
                                    }
                                    
                                    # Create forecast preview for chat
                                    forecast_df = pd.DataFrame(results.get('forecast_plot_data', {}))
                                    date_col = results.get('date_col_name', 'date')
                                    pred_col = results.get('pred_col_name', 'prediction')
                                    
                                    total_forecasted = results.get('kpi_1_value', 'N/A')
                                    model_name = results.get('kpi_3_value', 'N/A')
                                    
                                    # Get both interpretations
                                    interpretation_enhanced = results.get('interpretation_enhanced') or results.get('interpretation', '')
                                    interpretation_simple = results.get('interpretation_simple') or results.get('interpretation', '')
                                    
                                    # Default to enhanced
                                    interpretation = interpretation_enhanced
                                    
                                    # Calculate additional stats for display
                                    if not forecast_df.empty and pred_col in forecast_df.columns:
                                        avg_forecast = forecast_df[pred_col].mean()
                                        min_forecast = forecast_df[pred_col].min()
                                        max_forecast = forecast_df[pred_col].max()
                                        
                                        if date_col in forecast_df.columns:
                                            first_date = forecast_df[date_col].iloc[0]
                                            last_date = forecast_df[date_col].iloc[-1]
                                        else:
                                            first_date = 'N/A'
                                            last_date = 'N/A'
                                        
                                        # Format numeric values for display
                                        try:
                                            avg_str = f"{avg_forecast:,.2f}" if isinstance(avg_forecast, (int, float)) else str(avg_forecast)
                                            min_str = f"{min_forecast:,.2f}" if isinstance(min_forecast, (int, float)) else str(min_forecast)
                                            max_str = f"{max_forecast:,.2f}" if isinstance(max_forecast, (int, float)) else str(max_forecast)
                                        except:
                                            avg_str = str(avg_forecast) if avg_forecast is not None else 'N/A'
                                            min_str = str(min_forecast) if min_forecast is not None else 'N/A'
                                            max_str = str(max_forecast) if max_forecast is not None else 'N/A'
                                    else:
                                        avg_str = 'N/A'
                                        min_str = 'N/A'
                                        max_str = 'N/A'
                                        first_date = 'N/A'
                                        last_date = 'N/A'
                                    
                                    # Create preview response
                                    preview_response = f"""🔮 **Forecast Complete!**

**Summary:**
- **Model:** {model_name}
- **Prediction Steps:** {final_analysis['horizon_steps']}
- **Forecast Period:** {first_date} to {last_date}
- **Total Forecasted:** {total_forecasted}
- **Average:** {avg_str}
- **Min:** {min_str}
- **Max:** {max_str}
"""
                                    
                                    # Display preview in chat
                                    st.markdown(preview_response)
                                    
                                    # Business Insights View Selector
                                    st.markdown("---")
                                    st.markdown("### 💼 Business Insights View")
                                    
                                    # Check if both interpretations are available
                                    has_both = bool(results.get('interpretation_simple')) and bool(results.get('interpretation_enhanced'))
                                    
                                    if has_both:
                                        # Show radio buttons with Simple as default
                                        insight_style = st.radio(
                                            "Choose your business insights view:",
                                            ["Simple & Direct", "Enhanced Business View"],
                                            index=0,  # Default to Simple
                                            key=f"chat_insight_selector_{len(st.session_state.messages)}",
                                            horizontal=True
                                        )
                                        
                                        if insight_style == "Enhanced Business View":
                                            selected_interpretation = interpretation_enhanced
                                            style_badge = "💼 **Enhanced Business View**"
                                        else:
                                            selected_interpretation = interpretation_simple
                                            style_badge = "📝 **Simple & Direct**"
                                        
                                        st.markdown(style_badge)
                                        st.markdown("---")
                                        st.markdown(selected_interpretation)
                                        
                                        # Show info about the selected style
                                        if insight_style == "Enhanced Business View":
                                            st.info("💡 **Enhanced View:** Executive-friendly language with detailed pattern analysis, trends, and business recommendations.")
                                        else:
                                            st.info("💡 **Simple View:** Quick, concise summary with essential insights and recommendations.")
                                    else:
                                        # Only one available - show it with a note
                                        if results.get('interpretation_simple'):
                                            st.markdown("📝 **Simple & Direct**")
                                            st.markdown("---")
                                            st.markdown(interpretation_simple)
                                            st.info("ℹ️ Simple view available. Run a new forecast to get both styles.")
                                        elif results.get('interpretation_enhanced'):
                                            st.markdown("💼 **Enhanced Business View**")
                                            st.markdown("---")
                                            st.markdown(interpretation_enhanced)
                                            st.info("ℹ️ Enhanced view available. Run a new forecast to get both styles.")
                                        else:
                                            # Fallback to default interpretation
                                            st.markdown("**Interpretation:**")
                                            st.markdown("---")
                                            st.markdown(interpretation)
                                    
                                    st.markdown("---")
                                    st.markdown("💡 Check the **📊 Forecast Dashboard** tab for detailed analysis and download options.")
                                    
                                    # Show forecast chart preview
                                    if not forecast_df.empty and date_col in forecast_df.columns and pred_col in forecast_df.columns:
                                        try:
                                            # Ensure date column is datetime for proper chart display
                                            if not pd.api.types.is_datetime64_any_dtype(forecast_df[date_col]):
                                                forecast_df[date_col] = pd.to_datetime(forecast_df[date_col])
                                            
                                            plot_cols = [date_col, pred_col]
                                            for col in ['yhat_lower', 'yhat_upper', 'target_value']:
                                                if col in forecast_df.columns:
                                                    plot_cols.append(col)
                                            
                                            plot_cols = [col for col in plot_cols if col in forecast_df.columns]
                                            if len(plot_cols) >= 2:
                                                st.line_chart(forecast_df[plot_cols], x=date_col)
                                                
                                                # Show first few rows in expander
                                                with st.expander("📊 View Forecast Data (First 10 rows)"):
                                                    display_cols = [date_col, pred_col]
                                                    if 'yhat_lower' in forecast_df.columns:
                                                        display_cols.append('yhat_lower')
                                                    if 'yhat_upper' in forecast_df.columns:
                                                        display_cols.append('yhat_upper')
                                                    st.dataframe(forecast_df[display_cols].head(10))
                                        except Exception as chart_error:
                                            st.warning(f"Could not display forecast chart: {chart_error}")
                                    
                                    # Store forecast preview in message (include both interpretations)
                                    # Content without interpretation text since we render it interactively
                                    stored_content = preview_response + "\n\n💼 **Business Insights View**\n\nUse the selector below to choose your preferred interpretation style."
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": stored_content,
                                        "forecast_preview": {
                                            "forecast_df": forecast_df.to_dict('list') if not forecast_df.empty else {},
                                            "date_col": date_col,
                                            "pred_col": pred_col,
                                            "summary": {
                                                "total": total_forecasted,
                                                "model": model_name,
                                                "steps": final_analysis['horizon_steps'],
                                                "avg": avg_str,
                                                "min": min_str,
                                                "max": max_str,
                                                "first_date": str(first_date),
                                                "last_date": str(last_date)
                                            },
                                            "interpretation": interpretation,
                                            "interpretation_enhanced": interpretation_enhanced,
                                            "interpretation_simple": interpretation_simple
                                        }
                                    })
                                except Exception as e:
                                    # If there's an error displaying the preview, still show basic message
                                    error_response = f"🔮 Forecast complete! Check **📊 Forecast Dashboard** tab.\n\n⚠️ Error displaying preview: {str(e)}"
                                    st.markdown(error_response)
                                    st.session_state.messages.append({"role": "assistant", "content": error_response})
                            else:
                                assistant_response = "🔮 Forecast failed. Check logs."
                                st.markdown(assistant_response)
                                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

                        else:
                             assistant_response = f"The agent couldn't finalize the forecast plan. RAG output was incomplete or formatted incorrectly."
                             st.markdown(assistant_response)
                             st.session_state.messages.append({"role": "assistant", "content": assistant_response})

                    except Exception as e:
                        assistant_response = f"An unexpected error occurred during final RAG analysis: {e}"
                        st.markdown(assistant_response)
                        st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            
            # Route 3: Visualization
            elif intent == 'visualization' and ANALYTICS_AVAILABLE:
                with st.spinner("📊 Generating visualization..."):
                    try:
                        result = parse_analytics_request(
                            prompt,
                            st.session_state.processed_df,
                            st.session_state.column_purposes
                        )
                        analysis_type, results = result

                        if analysis_type == 'visualization':
                            if results.get('success', False):
                                # Display the visualization
                                if 'image' in results:
                                    try:
                                        image_data = base64.b64decode(results['image'])
                                        st.image(image_data, use_column_width=True)
                                        
                                        # Show explanation and details
                                        st.caption(f"📊 {results.get('chart_type', 'Chart')}")
                                        if 'columns' in results and results['columns']:
                                            st.caption(f"Columns: {', '.join(results['columns'])}")
                                        if 'explanation' in results:
                                            st.markdown(f"**Explanation:** {results['explanation']}")
                                        
                                        # Store in chat history
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": f"📊 Generated {results.get('chart_type', 'visualization')}",
                                            "visualization": results['image']
                                        })
                                    except Exception as e:
                                        response = f"📊 Error displaying visualization: {str(e)}"
                                        st.error(response)
                                        st.session_state.messages.append({"role": "assistant", "content": response})
                                else:
                                    response = "📊 Visualization generated but no image data returned."
                                    st.error(response)
                                    st.session_state.messages.append({"role": "assistant", "content": response})
                            else:
                                # 🟢 IMPROVED ERROR HANDLING
                                error_msg = results.get('error', 'Unknown error')
                                
                                # Provide helpful suggestions based on available columns
                                available_cols = st.session_state.processed_df.columns.tolist()
                                suggestion = f"\n\n💡 Try specifying columns like: {', '.join(available_cols[:3])}..."
                                
                                response = f"📊 Error generating visualization: {error_msg}{suggestion}"
                                st.error(response)
                                st.session_state.messages.append({"role": "assistant", "content": response})
                        else:
                            # Fallback to regular analytics
                            formatted = format_analytics_response(analysis_type, results)
                            response = f"✅ **Analytics** ({analysis_type})\n\n{formatted}"
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                            
                    except Exception as e:
                        response = f"📊 Unexpected error in visualization: {str(e)}"
                        st.error(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Route 4: General Question (Google RAG)
            else:
                if has_data:
                    # Use Google RAG for general data questions with context
                    df_summary = f"Dataset has {len(st.session_state.processed_df)} rows and {len(st.session_state.processed_df.columns)} columns: {', '.join(st.session_state.processed_df.columns.tolist()[:10])}"
                    context_prompt = f"{df_summary}\n\nUser question: {prompt}"
                    assistant_response = get_rag_response(context_prompt)
                else:
                    assistant_response = get_rag_response(prompt)
                
                st.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

            st.rerun()

with tab_dashboard:
    st.header("Forecast Dashboard")
    if st.session_state.current_forecast_data:
        results = st.session_state.current_forecast_data
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        col1.metric(label="Total Forecasted", value=results.get('kpi_1_value', 'N/A'))
        col2.metric(label="Model Selected", value=results.get('kpi_3_value', 'N/A'))
        col3.metric(label="Prediction Steps", value=results.get('horizon_steps_value', 'N/A'))
        
        st.markdown("---")
        
        # 1. Plotting the results
        plot_df_data = results.get('forecast_plot_data', {})
        if plot_df_data:
            plot_df = pd.DataFrame(plot_df_data)
            
            date_col = results.get('date_col_name', 'date')
            pred_col = results.get('pred_col_name', 'prediction')
            
            # Build column list for plotting
            plot_cols = [date_col, pred_col]
            
            # Add common Prophet/XGB output columns if they exist
            for col in ['yhat_lower', 'yhat_upper', 'target_value']:
                if col in plot_df.columns:
                    plot_cols.append(col)
            
            # Filter plot columns to only those available in the DataFrame
            plot_cols = [col for col in plot_cols if col in plot_df.columns]
            
            st.line_chart(plot_df[plot_cols], x=date_col)
            
            # 2. Display the data table (first 100 rows)
            st.subheader("Forecast Data Table (First 100 Rows)")
            st.dataframe(plot_df.head(100)) 

        
        st.subheader("Agent's Interpretation & Business Feedback")
        
        # Check what interpretations are available
        has_simple = bool(results.get('interpretation_simple'))
        has_enhanced = bool(results.get('interpretation_enhanced'))
        has_both = has_simple and has_enhanced
        
        # Debug info (can be removed later)
        if st.session_state.get('show_debug', False):
            with st.expander("🔍 Debug Info"):
                st.write("Available interpretations:")
                st.write(f"- Simple: {has_simple}")
                st.write(f"- Enhanced: {has_enhanced}")
                st.write(f"- Both: {has_both}")
                st.write(f"Keys in results: {list(results.keys())}")
        
        # User choice for interpretation style
        if has_both:
            # Both available - show toggle
            interpretation_style = st.radio(
                "Choose interpretation style:",
                ["Enhanced Business View", "Simple & Direct"],
                index=0,  # Default to Enhanced
                horizontal=True,
                key="interpretation_style_selector"
            )
        elif has_enhanced:
            # Only enhanced available
            interpretation_style = "Enhanced Business View"
            st.info("ℹ️ Only Enhanced Business View is available for this forecast. Run a new forecast to get both styles.")
        elif has_simple:
            # Only simple available
            interpretation_style = "Simple & Direct"
            st.info("ℹ️ Only Simple & Direct view is available for this forecast. Run a new forecast to get both styles.")
        else:
            # Fallback to old interpretation
            interpretation_style = "Enhanced Business View"
            st.warning("⚠️ This forecast was generated before the dual interpretation feature. Only the default interpretation is available.")
        
        # Get the selected interpretation (with fallback for backward compatibility)
        if interpretation_style == "Simple & Direct":
            interpretation_text = results.get('interpretation_simple') or results.get('interpretation', 'No interpretation provided.')
            style_label = "📝 Simple & Direct"
        else:
            interpretation_text = results.get('interpretation_enhanced') or results.get('interpretation', 'No interpretation provided.')
            style_label = "💼 Enhanced Business View"
        
        # Display selected interpretation
        st.markdown(f"**{style_label}**")
        st.markdown("---")
        st.markdown(interpretation_text)
        
        # Add helpful note
        if interpretation_style == "Enhanced Business View":
            st.markdown("---")
            st.info("💡 **Enhanced View:** Executive-friendly language with detailed pattern analysis, trends, and business recommendations.")
        else:
            st.markdown("---")
            st.info("💡 **Simple View:** Quick, concise summary with essential insights and recommendations.")
        
        st.markdown("---")
        df_data = results.get('forecast_df_data', {})
        if df_data:
            csv = pd.DataFrame(df_data).to_csv(index=False).encode('utf-8')
            st.download_button(label="Download Forecast Data (CSV)", data=csv, file_name="forecast_results.csv", mime="text/csv")
    else:
        st.info("Run a forecast in the 💬 Agent Chat tab to see results here.")

with tab_explorer:
    st.header("Data Explorer")
    
    if st.session_state.uploaded_file_df is not None:
        df = st.session_state.uploaded_file_df
        
        # Create sub-tabs for different EDA sections
        eda_tabs = st.tabs([
            "📋 Overview", 
            "📊 Statistics", 
            "🔍 Missing Data", 
            "📈 Distributions",
            "🔗 Correlations",
            "⚠️ Validation"
        ])
        
        # Tab 1: Overview
        with eda_tabs[0]:
            st.subheader("Dataset Overview")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Rows", f"{len(df):,}")
            col2.metric("Total Columns", len(df.columns))
            col3.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
            col4.metric("Duplicates", f"{df.duplicated().sum():,}")
            
            st.markdown("---")
            
            # Column Information
            st.subheader("Column Information")
            col_info = []
            for col in df.columns:
                col_info.append({
                    "Column": col,
                    "Type": str(df[col].dtype),
                    "Non-Null": f"{df[col].count():,}",
                    "Null": f"{df[col].isnull().sum():,}",
                    "Null %": f"{(df[col].isnull().sum() / len(df) * 100):.2f}%",
                    "Unique": f"{df[col].nunique():,}"
                })
            st.dataframe(pd.DataFrame(col_info), use_container_width=True)
            
            st.markdown("---")
            st.subheader("Raw Data Preview (First 100 rows)")
            st.dataframe(df.head(100), use_container_width=True)
        
        # Tab 2: Statistics
        with eda_tabs[1]:
            st.subheader("Descriptive Statistics")
            
            # Numerical columns
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            if len(num_cols) > 0:
                st.markdown("**Numerical Columns**")
                st.dataframe(df[num_cols].describe().T, use_container_width=True)
            
            st.markdown("---")
            
            # Categorical columns
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(cat_cols) > 0:
                st.markdown("**Categorical Columns - Value Counts**")
                selected_cat = st.selectbox("Select categorical column:", cat_cols)
                
                if selected_cat:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Top 10 values in {selected_cat}:**")
                        value_counts = df[selected_cat].value_counts().head(10)
                        st.dataframe(value_counts, use_container_width=True)
                    
                    with col2:
                        st.write(f"**Distribution of {selected_cat}:**")
                        fig = px.bar(
                            x=value_counts.index, 
                            y=value_counts.values,
                            labels={'x': selected_cat, 'y': 'Count'}
                        )
                        st.plotly_chart(fig, width="stretch")
        
        # Tab 3: Missing Data
        with eda_tabs[2]:
            st.subheader("Missing Data Analysis")
            
            missing = df.isnull().sum()
            missing_pct = (missing / len(df) * 100).round(2)
            
            missing_df = pd.DataFrame({
                'Column': missing.index,
                'Missing Count': missing.values,
                'Missing %': missing_pct.values
            }).sort_values('Missing Count', ascending=False)
            
            # Only show columns with missing data
            missing_df = missing_df[missing_df['Missing Count'] > 0]
            
            if len(missing_df) > 0:
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.dataframe(missing_df, use_container_width=True)
                
                with col2:
                    fig = px.bar(
                        missing_df, 
                        x='Column', 
                        y='Missing %',
                        title='Missing Data Percentage by Column'
                    )
                    st.plotly_chart(fig, width="stretch")
            else:
                st.success("✅ No missing data found in the dataset!")
            
            # Missing data heatmap
            if len(missing_df) > 0:
                st.markdown("---")
                st.subheader("Missing Data Pattern (First 100 rows)")
                
                # Create a binary matrix for missing values
                missing_matrix = df.head(100).isnull().astype(int)
                
                fig = px.imshow(
                    missing_matrix.T,
                    labels=dict(x="Row", y="Column", color="Missing"),
                    aspect="auto",
                    color_continuous_scale=['lightgreen', 'red']
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, width="stretch")
        
        # Tab 4: Distributions
        with eda_tabs[3]:
            st.subheader("Data Distributions")
            
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if len(num_cols) > 0:
                selected_num = st.selectbox("Select numerical column:", num_cols)
                
                if selected_num:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Histogram**")
                        fig = px.histogram(
                            df, 
                            x=selected_num,
                            nbins=30,
                            title=f'Distribution of {selected_num}'
                        )
                        st.plotly_chart(fig, width="stretch")
                    
                    with col2:
                        st.write("**Box Plot**")
                        fig = px.box(
                            df, 
                            y=selected_num,
                            title=f'Box Plot of {selected_num}'
                        )
                        st.plotly_chart(fig, width="stretch")
            else:
                st.info("No numerical columns available for distribution analysis.")
        
        # Tab 5: Correlations
        with eda_tabs[4]:
            st.subheader("Correlation Analysis")
            
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if len(num_cols) >= 2:
                # Correlation matrix
                corr_matrix = df[num_cols].corr()
                
                st.write("**Correlation Heatmap**")
                fig = px.imshow(
                    corr_matrix,
                    text_auto='.2f',
                    aspect="auto",
                    color_continuous_scale='RdBu_r',
                    title='Correlation Matrix'
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, width="stretch")
                
                st.markdown("---")
                
                # Scatter plot for selected variables
                st.write("**Scatter Plot Analysis**")
                col1, col2 = st.columns(2)
                
                with col1:
                    x_var = st.selectbox("X-axis:", num_cols, key='scatter_x')
                
                with col2:
                    y_var = st.selectbox("Y-axis:", num_cols, index=min(1, len(num_cols)-1), key='scatter_y')
                
                if x_var and y_var and x_var != y_var:
                    fig = px.scatter(
                        df, 
                        x=x_var, 
                        y=y_var,
                        trendline="ols",
                        title=f'{x_var} vs {y_var}'
                    )
                    st.plotly_chart(fig, width="stretch")
                    
                    # Show correlation coefficient
                    corr_value = df[[x_var, y_var]].corr().iloc[0, 1]
                    st.metric("Correlation Coefficient", f"{corr_value:.3f}")
            else:
                st.info("Need at least 2 numerical columns for correlation analysis.")
        
        # Tab 6: Validation
        with eda_tabs[5]:
            st.subheader("Data Validation Status")
            
            if st.session_state.validation_critical:
                st.error("🔴 Critical Issues Detected")
                for error in st.session_state.validation_critical:
                    st.error(f"- {error}")
            
            if st.session_state.validation_warnings:
                st.warning("⚠️ Warnings")
                for warning in st.session_state.validation_warnings:
                    st.warning(f"- {warning}")
            
            if not st.session_state.validation_critical and not st.session_state.validation_warnings:
                st.success("✅ No validation issues found!")
            
            st.markdown("---")
            
            if st.session_state.processed_df is not None:
                st.subheader("✅ Processed Data Preview")
                st.dataframe(st.session_state.processed_df.head(100), use_container_width=True)
            
            st.markdown("---")
            
            st.subheader("Schema Information")
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.text(buffer.getvalue())
    else:
        st.info("📁 Upload data in the sidebar to start exploring.")
