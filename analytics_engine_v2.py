"""
Analytics Engine - Data Analysis Toolkit
Provides pre-built analytics functions for common data operations
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import re
import matplotlib.pyplot as plt
import base64
from io import BytesIO  


class DataAnalytics:
    """Comprehensive data analytics toolkit"""
    
    def __init__(self, df: pd.DataFrame, column_purposes: Dict[str, str] = None):
        """
        Initialize DataAnalytics with a dataframe
        
        Args:
            df: Input DataFrame
            column_purposes: Mapping of column names to their purposes
                            (e.g., {'date_column': 'time_index', 'value_column': 'target_value'})
        """
        self.df = df
        self.column_purposes = column_purposes or {}
    
    def get_basic_stats(self) -> Dict[str, Any]:
        """Get basic statistical summary of the dataset"""
        try:
            numeric_df = self.df.select_dtypes(include=[np.number])
            
            stats = {
                "shape": {
                    "rows": len(self.df),
                    "columns": len(self.df.columns)
                },
                "columns": self.df.columns.tolist(),
                "dtypes": self.df.dtypes.astype(str).to_dict(),
                "missing_values": self.df.isnull().sum().to_dict(),
                "numeric_summary": numeric_df.describe().to_dict() if not numeric_df.empty else {},
                "memory_usage": f"{self.df.memory_usage(deep=True).sum() / 1024**2:.2f} MB"
            }
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def get_correlation_analysis(self) -> Dict[str, Any]:
        """Analyze correlations between numeric columns"""
        try:
            numeric_df = self.df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                return {"error": "No numeric columns found for correlation analysis"}
            
            corr_matrix = numeric_df.corr()
            
            # Find strongest correlations
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_value = corr_matrix.iloc[i, j]
                    corr_pairs.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": float(corr_value)
                    })
            
            # Sort by absolute correlation
            corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            
            return {
                "correlation_matrix": corr_matrix.to_dict(),
                "top_correlations": corr_pairs[:10],
                "numeric_columns": numeric_df.columns.tolist()
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_time_series_stats(self) -> Dict[str, Any]:
        """Analyze time series data if available"""
        try:
            # Try to find time column
            time_col = None
            for col, purpose in self.column_purposes.items():
                if purpose == 'time_index':
                    time_col = col
                    break
            
            if time_col is None:
                # Try to auto-detect datetime column
                for col in self.df.columns:
                    if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                        time_col = col
                        break
            
            if time_col is None:
                return {"error": "No time/date column found in the dataset"}
            
            # Ensure datetime
            df_copy = self.df.copy()
            df_copy[time_col] = pd.to_datetime(df_copy[time_col])
            df_copy = df_copy.sort_values(time_col)
            
            stats = {
                "time_column": time_col,
                "time_range": {
                    "start": str(df_copy[time_col].min()),
                    "end": str(df_copy[time_col].max()),
                    "duration_days": (df_copy[time_col].max() - df_copy[time_col].min()).days
                },
                "frequency_analysis": {}
            }
            
            # Analyze numeric columns over time
            numeric_cols = df_copy.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols:
                stats["frequency_analysis"][col] = {
                    "mean": float(df_copy[col].mean()),
                    "std": float(df_copy[col].std()),
                    "trend": "increasing" if df_copy[col].iloc[-1] > df_copy[col].iloc[0] else "decreasing"
                }
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def detect_outliers(self, column: str = None, method: str = "iqr") -> Dict[str, Any]:
        """Detect outliers in numeric columns"""
        try:
            numeric_df = self.df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                return {"error": "No numeric columns found"}
            
            outliers = {}
            
            for col in numeric_df.columns:
                if column and col != column:
                    continue
                
                data = numeric_df[col].dropna()
                
                if method == "iqr":
                    Q1 = data.quantile(0.25)
                    Q3 = data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    
                    outlier_mask = (data < lower_bound) | (data > upper_bound)
                    outlier_count = outlier_mask.sum()
                    
                    outliers[col] = {
                        "count": int(outlier_count),
                        "percentage": float(outlier_count / len(data) * 100),
                        "lower_bound": float(lower_bound),
                        "upper_bound": float(upper_bound)
                    }
            
            return {"outliers": outliers, "method": method}
        except Exception as e:
            return {"error": str(e)}
    
    def aggregate_data(self, group_by: str, agg_column: str, agg_func: str = "sum") -> Dict[str, Any]:
        """Aggregate data by a grouping column"""
        try:
            if group_by not in self.df.columns:
                return {"error": f"Column '{group_by}' not found"}
            
            if agg_column not in self.df.columns:
                return {"error": f"Column '{agg_column}' not found"}
            
            agg_functions = {
                "sum": "sum",
                "mean": "mean",
                "count": "count",
                "min": "min",
                "max": "max",
                "std": "std"
            }
            
            if agg_func not in agg_functions:
                return {"error": f"Aggregation function '{agg_func}' not supported"}
            
            agg_key = agg_functions[agg_func]
            aggregated_series = self.df.groupby(group_by)[agg_column].agg(agg_key)
            result = aggregated_series.reset_index()

            aggregated_column_name = f"{agg_column}_{agg_key}"
            result = result.rename(columns={agg_column: aggregated_column_name})
            
            return {
                "grouped_data": result.to_dict('records'),
                "group_by": group_by,
                "aggregated_column": aggregated_column_name,
                "original_column": agg_column,
                "function": agg_func
            }
        except Exception as e:
            return {"error": str(e)}
    
    def calculate_average(self, column_name: str = None) -> Dict[str, Any]:
        """Calculate average/mean for numeric columns"""
        try:
            numeric_df = self.df.select_dtypes(include=[np.number])
            
            if numeric_df.empty:
                return {"error": "No numeric columns found in the dataset"}
            
            # If specific column requested
            if column_name:
                if column_name not in self.df.columns:
                    return {"error": f"Column '{column_name}' not found"}
                
                if column_name not in numeric_df.columns:
                    return {"error": f"Column '{column_name}' is not numeric"}
                
                avg_value = self.df[column_name].mean()
                return {
                    "column": column_name,
                    "average": float(avg_value),
                    "count": int(self.df[column_name].count()),
                    "sum": float(self.df[column_name].sum()),
                    "min": float(self.df[column_name].min()),
                    "max": float(self.df[column_name].max())
                }
            
            # Calculate average for all numeric columns
            averages = {}
            for col in numeric_df.columns:
                averages[col] = {
                    "average": float(numeric_df[col].mean()),
                    "count": int(numeric_df[col].count()),
                    "sum": float(numeric_df[col].sum())
                }
            
            return {
                "averages": averages,
                "numeric_columns": numeric_df.columns.tolist()
            }
        except Exception as e:
            return {"error": str(e)}
              
    def generate_visualization(self, user_query: str) -> Dict[str, Any]:
        """
        Generates a visualization based on user query WITHOUT using LLM
        Uses keyword detection and smart defaults based on data types
        
        Args:
            user_query: Natural language request for visualization
            
        Returns:
            Dictionary containing visualization results
        """
        try:
            query_lower = user_query.lower()
            
            # 1. DETECT COLUMNS from query
            detected_columns = []
            # Remove quotes from query for better matching
            query_clean = query_lower.replace('"', '').replace("'", '')
            
            for col in self.df.columns:
                # Check if column name (case-insensitive) appears in query
                if col.lower() in query_clean:
                    detected_columns.append(col)
            
            print(f"🔍 Detected columns: {detected_columns}")
            
            # If no columns detected, use first available columns
            if not detected_columns:
                numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                cat_cols = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
                
                if numeric_cols:
                    detected_columns = [numeric_cols[0]]
                elif cat_cols:
                    detected_columns = [cat_cols[0]]
                else:
                    detected_columns = [self.df.columns[0]]
            
            # Safety check: ensure we have at least one column
            if not detected_columns or len(detected_columns) == 0:
                raise ValueError("No columns available for visualization. Please ensure your dataset has at least one column.")
            
            # 2. DETECT CHART TYPE from keywords
            chart_type = None
            chart_keywords = {
                'histogram': ['histogram', 'hist', 'distribution'],
                'scatter': ['scatter', 'scatter plot', 'relationship'],
                'bar': ['bar', 'bar chart', 'bar plot'],
                'line': ['line', 'line chart', 'line plot', 'trend', 'time series'],
                'pie': ['pie', 'pie chart'],
                'box': ['box', 'boxplot', 'box plot'],
                'heatmap': ['heatmap', 'correlation', 'corr']
            }
            
            for chart, keywords in chart_keywords.items():
                if any(keyword in query_lower for keyword in keywords):
                    chart_type = chart
                    break
            
            # 3. AUTO-SELECT CHART TYPE if not specified
            if chart_type is None:
                chart_type = self._auto_select_chart_type(detected_columns)
            
            print(f"📊 Chart type: {chart_type}")
            print(f"📊 Using columns: {detected_columns}")
            
            # 4. GENERATE THE VISUALIZATION
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'histogram':
                col = detected_columns[0]
                if self.df[col].dtype in ['object', 'category']:
                    # For categorical, convert to bar chart
                    value_counts = self.df[col].value_counts().head(15)
                    plt.bar(range(len(value_counts)), value_counts.values, color='skyblue')
                    plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
                    plt.ylabel('Count')
                else:
                    plt.hist(self.df[col].dropna(), bins=30, color='skyblue', edgecolor='black')
                    plt.ylabel('Frequency')
                plt.title(f"Distribution of {col}")
                plt.xlabel(col)
                
            elif chart_type == 'scatter':
                if len(detected_columns) < 2:
                    # Find a second numeric column
                    numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                    numeric_cols = [c for c in numeric_cols if c not in detected_columns]
                    if numeric_cols:
                        detected_columns.append(numeric_cols[0])
                    else:
                        raise ValueError("Need at least 2 numeric columns for scatter plot")
                
                x_col, y_col = detected_columns[0], detected_columns[1]
                plt.scatter(self.df[x_col], self.df[y_col], alpha=0.6, color='purple')
                plt.title(f"{x_col} vs {y_col}")
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, alpha=0.3)
                
            elif chart_type == 'bar':
                if len(detected_columns) == 1:
                    # Single column - show value counts
                    col = detected_columns[0]
                    value_counts = self.df[col].value_counts().head(15)
                    plt.bar(range(len(value_counts)), value_counts.values, color='orange')
                    plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
                    plt.title(f"Top 15 {col}")
                    plt.ylabel('Count')
                    plt.xlabel(col)
                else:
                    # Two columns - group by first, aggregate second
                    group_col, value_col = detected_columns[0], detected_columns[1]
                    
                    # Check if value_col is numeric
                    if pd.api.types.is_numeric_dtype(self.df[value_col]):
                        # Numeric column - use mean
                        grouped = self.df.groupby(group_col)[value_col].mean().sort_values(ascending=False).head(15)
                        plt.bar(range(len(grouped)), grouped.values, color='orange')
                        plt.xticks(range(len(grouped)), grouped.index, rotation=45, ha='right')
                        plt.title(f"Average {value_col} by {group_col}")
                        plt.ylabel(f"Average {value_col}")
                    else:
                        # Categorical column - use count
                        grouped = self.df.groupby(group_col)[value_col].count().sort_values(ascending=False).head(15)
                        plt.bar(range(len(grouped)), grouped.values, color='orange')
                        plt.xticks(range(len(grouped)), grouped.index, rotation=45, ha='right')
                        plt.title(f"Count of {value_col} by {group_col}")
                        plt.ylabel(f"Count of {value_col}")
                    plt.xlabel(group_col)
                
            elif chart_type == 'line':
                if len(detected_columns) < 2:
                    # Find a second numeric column
                    numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
                    numeric_cols = [c for c in numeric_cols if c not in detected_columns]
                    if numeric_cols:
                        detected_columns.append(numeric_cols[0])
                    else:
                        raise ValueError("Need at least 2 columns for line plot")
                
                x_col, y_col = detected_columns[0], detected_columns[1]
                sorted_df = self.df.sort_values(x_col)
                plt.plot(sorted_df[x_col], sorted_df[y_col], linewidth=2, color='green', marker='o', markersize=4)
                plt.title(f"{y_col} over {x_col}")
                plt.xlabel(x_col)
                plt.ylabel(y_col)
                plt.grid(True, alpha=0.3)
                
            elif chart_type == 'pie':
                col = detected_columns[0]
                value_counts = self.df[col].value_counts().head(10)
                colors = plt.cm.Set3(range(len(value_counts)))
                plt.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%', 
                    startangle=90, colors=colors)
                plt.title(f"Distribution of {col}")
                
            elif chart_type == 'box':
                col = detected_columns[0]
                if self.df[col].dtype in ['object', 'category']:
                    raise ValueError(f"Cannot create boxplot for categorical column '{col}'")
                plt.boxplot(self.df[col].dropna(), vert=True, patch_artist=True,
                        boxprops=dict(facecolor='lightblue'))
                plt.ylabel(col)
                plt.title(f"Boxplot of {col}")
                plt.xticks([1], [col])
                
            elif chart_type == 'heatmap':
                # Use all numeric columns for correlation heatmap
                numeric_df = self.df.select_dtypes(include=[np.number])
                if numeric_df.empty:
                    raise ValueError("No numeric columns for heatmap")
                
                corr_matrix = numeric_df.corr()
                
                # Use matplotlib's imshow for heatmap
                im = plt.imshow(corr_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
                plt.colorbar(im)
                
                # Set ticks
                plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns, rotation=45, ha='right')
                plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)
                
                # Add correlation values as text
                for i in range(len(corr_matrix)):
                    for j in range(len(corr_matrix)):
                        plt.text(j, i, f'{corr_matrix.iloc[i, j]:.2f}',
                            ha='center', va='center', color='black', fontsize=8)
                
                plt.title("Correlation Heatmap")
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            # Generate simple explanation
            explanation = self._generate_explanation(chart_type, detected_columns)
            
            return {
                'success': True,
                'chart_type': chart_type,
                'columns': detected_columns,
                'explanation': explanation,
                'image': image_base64
            }
            
        except Exception as e:
            plt.close()
            return {
                'success': False,
                'error': f"Visualization error: {str(e)}"
            }
    
   
    def _auto_select_chart_type(self, columns: List[str]) -> str:
        """
        Automatically select chart type based on column data types
        """
        if not columns:
            return 'bar'
        
        col = columns[0]
        col_dtype = self.df[col].dtype
        
        # Single column logic
        if len(columns) == 1:
            if col_dtype in ['object', 'category']:
                return 'bar'  # Categorical -> bar chart
            else:
                return 'histogram'  # Numeric -> histogram
        
        # Two+ columns logic
        else:
            col1_dtype = self.df[columns[0]].dtype
            col2_dtype = self.df[columns[1]].dtype
            
            if col1_dtype in ['object', 'category'] and col2_dtype in [np.number, 'int64', 'float64']:
                return 'bar'  # Categorical + Numeric -> bar
            elif col1_dtype in [np.number, 'int64', 'float64'] and col2_dtype in [np.number, 'int64', 'float64']:
                return 'scatter'  # Numeric + Numeric -> scatter
            else:
                return 'bar'
    
    def _generate_explanation(self, chart_type: str, columns: List[str]) -> str:
        """
        Generate simple explanation for the visualization
        """
        # Safety check: ensure columns list is not empty
        if not columns:
            return f"Visualization of {chart_type}"
        
        # Get column names safely
        col0 = columns[0] if len(columns) > 0 else "column"
        col1 = columns[1] if len(columns) > 1 else "column"
        
        explanations = {
            'histogram': f"This histogram shows the distribution of values in {col0}. The x-axis represents the value ranges, and the y-axis shows the frequency of observations in each range.",
            'scatter': f"This scatter plot shows the relationship between {col0} and {col1}. Each point represents one observation. Look for patterns like positive/negative correlation or clusters.",
            'bar': f"This bar chart displays {'the frequency of different categories' if len(columns) == 1 else f'the distribution of {col1} for each {col0}'} in the dataset.",
            'line': f"This line chart shows the trend of {col1} over {col0}. Useful for identifying patterns, trends, or changes over time.",
            'pie': f"This pie chart shows the proportion of different categories in {col0}. Each slice represents the percentage of the total.",
            'box': f"This box plot displays the distribution and outliers for {col0}. The box shows the quartiles, and the whiskers extend to show the data range.",
            'heatmap': "This heatmap shows the correlation between all numeric variables. Colors indicate the strength and direction of relationships: red for positive correlation, blue for negative."
        }
        return explanations.get(chart_type, f"Visualization of {', '.join(columns)}")



    def detect_performance_deviations(
        self, 
        value_column: str, 
        group_by_column: str, 
        threshold_std: float = 2.0
        ) -> Dict[str, Any]:
            """
            Identifies major bottlenecks/risks by finding values that significantly
            deviate (based on standard deviation) from the group mean.
            
            Args:
                value_column: The metric to check (e.g., 'Lead Time', 'Cost').
                group_by_column: The dimension to aggregate by (e.g., 'Supplier ID', 'Destination').
                threshold_std: How many standard deviations away from the mean is considered a risk.
            """
            try:
                if value_column not in self.df.columns or group_by_column not in self.df.columns:
                    return {"error": "One or both specified columns not found in the DataFrame."}
                
                # Calculate group statistics (mean and std)
                stats = self.df.groupby(group_by_column)[value_column].agg(['mean', 'std', 'count']).reset_index()
                
                # Calculate the Z-score or deviation boundary for each group
                stats['upper_bound'] = stats['mean'] + (stats['std'] * threshold_std)
                stats['lower_bound'] = stats['mean'] - (stats['std'] * threshold_std)
                
                # Identify severe deviations
                deviations = self.df.copy()
                deviations = deviations.merge(stats, on=group_by_column, how='left')
                
                # Flag records that exceed boundaries
                deviations['is_risk'] = (
                    (deviations[value_column] > deviations['upper_bound']) | 
                    (deviations[value_column] < deviations['lower_bound'])
                )
                
                risk_records = deviations[deviations['is_risk']].copy()
                
                if risk_records.empty:
                    return {"message": f"No significant deviations (over {threshold_std} std) found in {value_column} by {group_by_column}."}

                # Summarize the risks
                summary = risk_records.groupby(group_by_column)[value_column].agg(
                    risk_count='count', 
                    avg_deviation=lambda x: (x - deviations.loc[x.index, 'mean']).abs().mean()
                ).reset_index()
                
                # Merge summary back with group stats for context
                final_report = summary.merge(stats[[group_by_column, 'mean', 'std']], on=group_by_column)
                
                return {
                    "risk_metric": value_column,
                    "grouping_dimension": group_by_column,
                    "threshold_std": threshold_std,
                    "top_risks": final_report.sort_values(by='risk_count', ascending=False).head(10).to_dict('records')
                }
            except Exception as e:
                return {"error": f"Deviation detection failed: {str(e)}"}
        

def parse_analytics_request(query: str, df: pd.DataFrame, column_purposes: Dict[str, str]) -> Tuple[str, Dict[str, Any]]:
    """
    Parse user query and route to appropriate analytics function
    
    Returns:
        Tuple of (analysis_type, results)
    """
    query_lower = query.lower()
    analytics = DataAnalytics(df, column_purposes)
    
     # 🟢 IMPROVED: Extract column names from query (adding this part)
    detected_columns = []
    for col in df.columns:
        if col.lower() in query_lower:
            detected_columns.append(col)
    
    print(f"🔍 Query Analysis: '{query}' -> Detected columns: {detected_columns}")
    
    def contains_keyword(text: str, keywords: List[str]) -> bool:
        return any(re.search(rf"\b{re.escape(word)}\b", text) for word in keywords)

    # Average/Mean calculation (CHECK THIS FIRST - more specific)
    if any(word in query_lower for word in ['average', 'mean', 'avg']):
        numeric_cols_df = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_detected = [col for col in detected_columns if col in numeric_cols_df]
        non_numeric_detected = [col for col in detected_columns if col not in numeric_cols_df]

        column_name = None
        # Prefer explicitly detected numeric column
        if numeric_detected:
            column_name = numeric_detected[0]
        else:
            # Try to match the first column mentioned in the query
            for col in df.columns:
                if col.lower() in query_lower and col in numeric_cols_df:
                    column_name = col
                    break

        # Detect grouping intent (“by”, “per”, “for each” etc.)
        has_grouping_keyword = any(
            phrase in query_lower
            for phrase in [' by ', ' per ', ' for each ', ' grouped by ', ' group by ']
        )
        group_column = None
        if has_grouping_keyword and len(detected_columns) >= 2:
            # Pick the first non-numeric detected column as the grouping column
            for col in detected_columns:
                if col in non_numeric_detected:
                    group_column = col
                    break

        if group_column and column_name:
            return 'aggregation', analytics.aggregate_data(
                group_by=group_column,
                agg_column=column_name,
                agg_func="mean"
            )

        # Fallback to simple average
        return 'average', analytics.calculate_average(column_name)
    
    # Check for visualization requests (after ensuring it's not a numeric summary request)
    visualization_keywords = [
        'plot', 'chart', 'graph', 'visualize', 'visualization',
        'data visualization', 'create visualization', 'generate visualization',
        'histogram', 'scatter', 'bar chart', 'line chart', 'pie chart', 'boxplot', 'heatmap'
    ]
    if contains_keyword(query_lower, visualization_keywords):
        return 'visualization', analytics.generate_visualization(query)
    
    # Basic statistics
    elif any(word in query_lower for word in ['statistics', 'stats', 'summary', 'describe']):
        return 'basic_stats', analytics.get_basic_stats()
    
    # Correlation analysis
    elif any(word in query_lower for word in ['correlation', 'correlate', 'relationship']):
        return 'correlation', analytics.get_correlation_analysis()
    
    # Time series
    elif any(word in query_lower for word in ['time series', 'trend', 'over time', 'temporal']):
        return 'time_series', analytics.get_time_series_stats()
    
    # Outliers
    elif any(word in query_lower for word in ['outlier', 'anomaly', 'unusual']):
        return 'outliers', analytics.detect_outliers()
    elif any(word in query_lower for word in ['risk', 'bottleneck', 'deviation', 'worst performer', 'issue']):
        
        # Attempt to extract value and grouping column based on common SCM terms
        value_col = None
        group_col = None
        
        # Simple heuristic: look for keywords tied to known columns (requires manual mapping or LLM context in a real system)
        
        # For a basic implementation, we'll default to the most common SCM metrics if the user implies risk:
        
        # Heuristic 1: Try to find a metric column name
        potential_values = ['lead_time', 'delivery_time', 'cost', 'fulfillment_rate', 'delay']
        for val in potential_values:
            if val in query_lower or any(c.lower() in query_lower for c in df.columns if val in c.lower()):
                # If a likely value column is mentioned, try to infer the group
                value_col = next((c for c in df.columns if val in c.lower()), None)
                break
        
        # Heuristic 2: Try to find a grouping column (Supplier, Product, Warehouse)
        potential_groups = ['supplier', 'product', 'warehouse', 'location', 'customer']
        for group in potential_groups:
            if group in query_lower or any(c.lower() in query_lower for c in df.columns if group in c.lower()):
                group_col = next((c for c in df.columns if group in c.lower()), None)
                break
        
        # If we found the necessary parts, call the new function
        if value_col and group_col:
             return 'deviation', analytics.detect_performance_deviations(
                value_column=value_col,
                group_by_column=group_col
            )
        
        # Fallback if context is missing (Ask user for clarification or return basic stats)
        if not value_col or not group_col:
             return 'basic_stats', analytics.get_basic_stats() # Or prompt the user to specify columns
        
    
    # Default to basic stats
    else:
        return 'basic_stats', analytics.get_basic_stats()
    

def format_analytics_response(analysis_type: str, results: Dict[str, Any]) -> str:
    """Format analytics results into readable text"""
    
    if "error" in results:
        return f"❌ Error: {results['error']}"
    
    if analysis_type == 'basic_stats':
        shape = results.get('shape', {})
        response = f"""
    **Dataset Statistics:**

    📊 **Shape:** {shape.get('rows', 'N/A')} rows × {shape.get('columns', 'N/A')} columns

    📋 **Columns:** {len(results.get('columns', []))} total

    🔢 **Data Types:**
    {chr(10).join(f"  • {col}: {dtype}" for col, dtype in list(results.get('dtypes', {}).items())[:10])}

    ⚠️ **Missing Values:** {sum(results.get('missing_values', {}).values())} total

    💾 **Memory Usage:** {results.get('memory_usage', 'N/A')}
    """
        return response
    
    elif analysis_type == 'correlation':
        top_corr = results.get('top_correlations', [])[:5]
        response = "**Correlation Analysis:**\n\n"
        response += "🔗 **Top Correlations:**\n"
        for item in top_corr:
            corr_emoji = "🟢" if item['correlation'] > 0 else "🔴"
            response += f"{corr_emoji} {item['column1']} ↔ {item['column2']}: {item['correlation']:.3f}\n"
        return response
    
    elif analysis_type == 'time_series':
        time_range = results.get('time_range', {})
        response = f"""
    **Time Series Analysis:**

    📅 **Time Range:**
    • Start: {time_range.get('start', 'N/A')}
    • End: {time_range.get('end', 'N/A')}
    • Duration: {time_range.get('duration_days', 'N/A')} days

    📈 **Trends:**
    """
        for col, stats in results.get('frequency_analysis', {}).items():
            response += f"\n  • {col}: {stats.get('trend', 'N/A')} (μ={stats.get('mean', 0):.2f}, σ={stats.get('std', 0):.2f})"
        
        return response
    
    elif analysis_type == 'outliers':
        outliers = results.get('outliers', {})
        response = "**Outlier Detection:**\n\n"
        for col, stats in outliers.items():
            response += f"📍 **{col}:** {stats['count']} outliers ({stats['percentage']:.2f}%)\n"
            response += f"   Range: [{stats['lower_bound']:.2f}, {stats['upper_bound']:.2f}]\n\n"
        return response
    
    elif analysis_type == 'average':
        # Check if single column or multiple
        if 'column' in results:
            # Single column average
            response = f"""
    **Average Calculation:**

    📊 **Column:** {results['column']}
    📈 **Average:** {results['average']:,.2f}
    📍 **Count:** {results['count']:,} values
    ➕ **Sum:** {results['sum']:,.2f}
    🔽 **Min:** {results['min']:,.2f}
    🔼 **Max:** {results['max']:,.2f}
    """
            return response
        else:
            # Multiple columns
            response = "**Average for All Numeric Columns:**\n\n"
            for col, stats in results.get('averages', {}).items():
                response += f"📊 **{col}:**\n"
                response += f"  • Average: {stats['average']:,.2f}\n"
                response += f"  • Count: {stats['count']:,}\n"
                response += f"  • Sum: {stats['sum']:,.2f}\n\n"
            return response
    
    elif analysis_type == 'aggregation':
        grouped = results.get('grouped_data', [])
        group_by = results.get('group_by', 'Group')
        agg_col = results.get('aggregated_column', 'Value')
        func = results.get('function', 'mean')

        if not grouped:
            return f"No aggregation results available for {agg_col} by {group_by}."

        header = f"**{func.title()} of {agg_col} by {group_by}:**\n\n"
        lines = []
        for item in grouped:
            group_value = item.get(group_by, 'N/A')
            metric_value = item.get(agg_col, 'N/A')
            lines.append(f"- **{group_value}:** {metric_value:,.2f}" if isinstance(metric_value, (int, float)) else f"- **{group_value}:** {metric_value}")
        return header + "\n".join(lines)
        
    elif analysis_type == 'deviation':
        top_risks = results.get('top_risks', [])
        metric = results.get('risk_metric', 'Metric')
        group = results.get('grouping_dimension', 'Dimension')
        threshold = results.get('threshold_std', 2.0)
        
        response = f"""
    ⚠️ **PERFORMANCE RISK ALERT: Top Bottlenecks Detected** ⚠️

    This analysis highlights performance points that deviate significantly from the norm for their group.
    Metric Analyzed: `{metric}`
    Grouping By: `{group}`
    Risk Threshold: > {threshold:.1f} Standard Deviations outside the mean.

    ---
    """
        if not top_risks:
            response += "🎉 Great news! No significant deviations found based on the threshold."
            return response

        response += "🔥 **Top 10 Most Deviant Groups:**\n"
        for item in top_risks:
            group_id = item[group]
            risk_count = item['risk_count']
            avg_dev = item['avg_deviation']
            mean = item['mean']
            
            response += f"\n➡️ **{group_id}** (Count: {risk_count}):\n"
            response += f"   • Average {metric}: {mean:,.2f}\n"
            response += f"   • Avg. Deviation Magnitude: {avg_dev:,.2f}\n"
            
        return response  
    
    else:
        return str(results)

