import pandas as pd

# This schema is simple. It just defines the *purpose* of the columns
# our app needs.
SCHEMA_REGISTRY = {
    "supply_chain_schema": {
        "required_columns_by_purpose": {
            "time_index": {
                "expected_type": "datetime",
                "description": "The main date/time column for the forecast."
            },
            "target_value": {
                "expected_type": "numeric",
                "description": "The main numerical value to be forecasted (e.g., Sales, Quantity)."
            }
        },
        "optional_columns_by_purpose": {
            "regressor": {
                "expected_type": "any",
                "description": "Optional features to help the forecast (e.g., promotions, store ID)."
            },
            "holiday": {
                "expected_type": "string",
                "description": "Names of holidays, if available."
            }
        }
    }
}

def load_schema(schema_id: str) -> dict | None:
    """Loads a validation schema from the registry."""
    return SCHEMA_REGISTRY.get(schema_id)

def validate_dataframe(df: pd.DataFrame, schema: dict, mapped_columns: dict) -> (bool, pd.DataFrame, list, list):
    """
    Validates a DataFrame against a schema using a pre-defined mapping.
    It now uses 'Critical' for blocking errors and 'Warning' for fixable issues.
    """
    warnings = []
    critical = []
    df_processed = df.copy()
    
    if not schema or "required_columns_by_purpose" not in schema:
        critical.append("Critical: Schema is missing or invalid.")
        return False, df, warnings, critical
        
    required_purposes = schema["required_columns_by_purpose"]

    # 1. Check if all required purposes are mapped
    for purpose in required_purposes.keys():
        if purpose not in mapped_columns or not mapped_columns[purpose]:
            critical.append(f"Critical: No column was mapped for the required purpose: '{purpose}'.")
    
    if critical:
        return False, df, warnings, critical 

    # 2. Apply type conversions and check for errors
    for purpose, col_name in mapped_columns.items():
        if col_name not in df_processed.columns:
            critical.append(f"Critical: Mapped column '{col_name}' for purpose '{purpose}' not found in data.")
            continue
            
        if purpose not in required_purposes and purpose not in mapped_columns.get('regressors', []):
            continue 

        target_type = required_purposes.get(purpose, {}).get("expected_type", "string")
        
        try:
            original_nulls = df_processed[col_name].isnull().sum()
            
            # --- AGGRESSIVE TYPE CASTING FIX ---
            if purpose == "time_index" or target_type == "datetime":
                df_processed[col_name] = pd.to_datetime(df_processed[col_name], errors='coerce')
                
            elif purpose == "target_value" or target_type in ["float", "numeric", "integer"]:
                # --- FIX: Aggressively convert to numeric ---
                df_processed[col_name] = pd.to_numeric(df_processed[col_name], errors='coerce')
                
                # If target is integer, convert to the nullable integer type
                if target_type == "integer":
                    df_processed[col_name] = df_processed[col_name].astype('Int64', errors='ignore')
                    
            elif target_type == "string":
                df_processed[col_name] = df_processed[col_name].astype(str)
            
            # Check if conversion created new nulls
            new_nulls = df_processed[col_name].isnull().sum()
            if new_nulls > original_nulls:
                warnings.append(f"Warning: Column '{col_name}' (for '{purpose}') had invalid values that were set to Null.")

        except Exception as type_e:
            critical.append(f"Critical: Failed to convert column '{col_name}' to type '{target_type}'. Cannot proceed.")

    # 3. Check for final nulls in key columns (now classified as Warnings)
    time_col = mapped_columns.get('time_index')
    target_col = mapped_columns.get('target_value')
    
    if time_col and df_processed[time_col].isnull().any():
        warnings.append(f"Warning: The date column '{time_col}' contains missing values. These rows will be ignored.")
    
    if target_col and df_processed[target_col].isnull().any():
        warnings.append(f"Warning: The target column '{target_col}' contains missing values. These rows will be ignored.")

    is_valid = not critical # True if no Critical errors exist
    
    return is_valid, df_processed, warnings, critical