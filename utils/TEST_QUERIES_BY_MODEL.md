# Test Queries for Each Model

## Model Differentiation Summary

| Model | Frequency | Categorical Features | Target | Key Features | When to Use |
|-------|-----------|---------------------|--------|--------------|-------------|
| **LightGBM** | Daily (D) | ✅ Customer/Location/BusinessType | TotalRevenue | Lags: 1,7,14 days<br>Rolling: 7,14 days | Daily data with categoricals |
| **XGBoost** | Monthly (M/ME) | ✅ Customer/Location/BusinessType | NumberOfPieces | Lags: 1,3,6 months<br>Rolling: 3,6,12 months | Monthly data with categoricals |
| **LSTM** | Daily (D) | ❌ No categoricals | Various | Deep learning<br>Sequence learning | Daily without categoricals OR explicit deep learning request |
| **SARIMA** | Daily (D) | ❌ No categoricals | TotalRevenue | Weekly seasonality (period=7)<br>Statistical model | Daily univariate with weekly patterns |
| **Prophet** | Weekly (W) | ❌ No categoricals | OrderCount | Strong seasonality<br>Time-series stats | Weekly data |

---

## Test Queries by Model

### 1. LightGBM Model (`lightgbm_model`)

**Expected Selection:** Daily data + Customer/Location/BusinessType columns

#### Query 1 (Simple & Direct):
```
"Forecast daily TotalRevenue for the next 30 days. I have Customer, Location, and BusinessType columns."
```

#### Query 2 (With Feature Details):
```
"Predict daily revenue for next 2 weeks. My data includes Customer, Location, BusinessType, OrderCount, and NumberOfPieces."
```

#### Query 3 (Explicit Daily):
```
"Run a daily forecast for TotalRevenue for the next 21 days. Data has Customer and Location columns."
```

#### Query 4 (Simple):
```
"Forecast daily TotalRevenue for next 14 days."
```

#### Query 5 (With Lag Mention):
```
"Generate a daily forecast with lag features for TotalRevenue. Forecast next 30 days. I have Customer, Location, and BusinessType."
```

**Expected Response:**
```json
{
  "model_id": "lightgbm_model",
  "horizon_steps": 30,
  "target_col": "TotalRevenue",
  "regressor_cols": ["Customer", "Location", "BusinessType"],
  "frequency": "D"
}
```

---

### 2. XGBoost Model (`xgboost_v1`)

**Expected Selection:** Monthly data + Customer/Location/BusinessType columns

#### Query 1 (Monthly with Categoricals):
```
"Forecast monthly NumberOfPieces for the next 6 months. My data has Customer, Location, and BusinessType columns."
```

#### Query 2 (Multiple Locations):
```
"Predict NumberOfPieces for next 12 months. I have multiple locations and customers in my data."
```

#### Query 3 (With Rolling Stats):
```
"Generate a monthly forecast with rolling statistics for NumberOfPieces. Forecast next 6 months. Data includes Customer, Location, BusinessType."
```

#### Query 4 (Explicit Monthly):
```
"Run a monthly forecast for NumberOfPieces for next 3 months. I have Customer and Location columns."
```

#### Query 5 (Complex Monthly):
```
"Forecast monthly NumberOfPieces with lag features and rolling averages. Next 6 months. Data has Customer, Location, BusinessType, TotalRevenue."
```

**Expected Response:**
```json
{
  "model_id": "xgboost_v1",
  "horizon_steps": 6,
  "target_col": "NumberOfPieces",
  "regressor_cols": ["Customer", "Location", "BusinessType"],
  "frequency": "M"
}
```

---

### 3. LSTM Model (`lstm_v1`)

**Expected Selection:** Daily data WITHOUT Customer/Location/BusinessType OR explicit deep learning request

#### Query 1 (Daily without Categoricals):
```
"Forecast daily revenue for the next 30 days. I only have date and revenue columns."
```

#### Query 2 (Explicit Deep Learning):
```
"Use deep learning to predict daily revenue for next 2 weeks."
```

#### Query 3 (Neural Network Mention):
```
"Run a forecast using neural network for daily data. Predict next 21 days."
```

#### Query 4 (LSTM Mention):
```
"Use LSTM to forecast daily revenue for next 14 days."
```

#### Query 5 (Sequence Learning):
```
"Predict daily revenue using sequence learning. Forecast next 30 days."
```

**Expected Response:**
```json
{
  "model_id": "lstm_v1",
  "horizon_steps": 30,
  "target_col": "TotalRevenue",
  "regressor_cols": [],
  "frequency": "D"
}
```

---

### 4. SARIMA Model (`sarima_daily_v1`)

**Expected Selection:** Daily data + Weekly seasonality + Statistical model + NO categoricals

#### Query 1 (Weekly Seasonality):
```
"Forecast daily TotalRevenue for the next 30 days. The data shows weekly seasonal patterns."
```

#### Query 2 (Statistical Model):
```
"Use a statistical time series model to predict daily revenue for next 2 weeks with weekly seasonality."
```

#### Query 3 (SARIMA Mention):
```
"Run a SARIMA forecast for daily TotalRevenue. Forecast next 21 days. Data has weekly patterns."
```

#### Query 4 (Univariate):
```
"Forecast daily revenue using a univariate time series model with weekly seasonality. Next 14 days."
```

#### Query 5 (Seasonal ARIMA):
```
"Predict daily TotalRevenue for next 30 days using seasonal ARIMA. The data has weekly seasonal components."
```

**Expected Response:**
```json
{
  "model_id": "sarima_daily_v1",
  "horizon_steps": 30,
  "target_col": "TotalRevenue",
  "regressor_cols": [],
  "frequency": "D"
}
```

---

### 5. Prophet Model (`prophet_weekly_v1`)

**Expected Selection:** Weekly data frequency

#### Query 1 (Weekly Data):
```
"Forecast weekly OrderCount for the next 12 weeks."
```

#### Query 2 (Weekly Seasonality):
```
"Predict weekly order volume for next 24 weeks. The data has strong weekly seasonality."
```

#### Query 3 (Prophet Mention):
```
"Use Prophet to forecast weekly OrderCount for next 8 weeks."
```

#### Query 4 (Weekly Patterns):
```
"Generate a weekly forecast for OrderCount. Forecast next 16 weeks with seasonality."
```

#### Query 5 (Weekly Frequency):
```
"Forecast weekly data for next 12 weeks. Target is OrderCount."
```

**Expected Response:**
```json
{
  "model_id": "prophet_weekly_v1",
  "horizon_steps": 12,
  "target_col": "OrderCount",
  "regressor_cols": [],
  "frequency": "W"
}
```

---

## Quick Reference: Model Selection Rules

1. **Weekly data?** → Prophet
2. **Monthly + Customer/Location/BusinessType?** → XGBoost
3. **Daily + Customer/Location/BusinessType?** → LightGBM
4. **Daily + NO categoricals + Deep learning mention?** → LSTM
5. **Daily + NO categoricals + Weekly seasonality?** → SARIMA

---

## Testing Tips

1. **Upload appropriate data first** - Make sure your test data matches the model requirements
2. **Check data frequency** - The RAG detects frequency from your data structure
3. **Verify categorical columns** - Ensure Customer/Location/BusinessType are present for LightGBM/XGBoost
4. **Use specific keywords** - Mentioning "deep learning", "weekly seasonality", "monthly", etc. helps
5. **Check the response** - Verify the `model_id` in the JSON response matches your expectation

