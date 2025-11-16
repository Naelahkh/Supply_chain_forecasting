# Model Selection Guide & Test Queries

## Model Differentiation

### 1. **LightGBM Model** (`lightgbm_model`)
**When to Use:**
- ✅ **DAILY** data frequency
- ✅ Has **Customer, Location, BusinessType** columns
- ✅ Target: **TotalRevenue**
- ✅ Features: Lag (1, 7, 14 days), Rolling stats (7, 14 days)
- ✅ Can use: OrderCount, NumberOfPieces as features

**Key Differentiator:** DAILY + Categorical features (Customer/Location/BusinessType)

---

### 2. **XGBoost Model** (`xgboost_v1`)
**When to Use:**
- ✅ **MONTHLY** data frequency
- ✅ Has **Customer, Location, BusinessType** columns
- ✅ Target: **NumberOfPieces**
- ✅ Features: Lag (1, 3, 6 months), Rolling stats (3, 6, 12 months)

**Key Differentiator:** MONTHLY + Categorical features (Customer/Location/BusinessType)

---

### 3. **LSTM Model** (`lstm_v1`)
**When to Use:**
- ✅ **DAILY** data frequency
- ❌ **NO** Customer/Location/BusinessType columns (or user explicitly wants deep learning)
- ✅ Uses deep learning/neural networks
- ✅ Sequence learning approach

**Key Differentiator:** DAILY + NO categorical features OR explicit deep learning request

---

### 4. **SARIMA Model** (`sarima_daily_v1`)
**When to Use:**
- ✅ **DAILY** data frequency
- ❌ **NO** categorical features needed
- ✅ Univariate time series (single target variable)
- ✅ Weekly seasonality patterns (period=7)
- ✅ Statistical time series model

**Key Differentiator:** DAILY + Univariate + Weekly seasonality + Statistical model

---

### 5. **Prophet Model** (`prophet_weekly_v1`)
**When to Use:**
- ✅ **WEEKLY** data frequency
- ✅ Strong seasonality patterns
- ✅ Time-series statistical methods

**Key Differentiator:** WEEKLY frequency

---

## Decision Tree Summary

```
Is data WEEKLY?
  YES → Prophet (prophet_weekly_v1)
  NO → Continue

Is data MONTHLY?
  YES → Has Customer/Location/BusinessType?
    YES → XGBoost (xgboost_v1)
    NO → (Not supported - use daily models)
  NO → Continue

Is data DAILY?
  YES → Has Customer/Location/BusinessType?
    YES → LightGBM (lightgbm_model)
    NO → User wants deep learning/neural network?
      YES → LSTM (lstm_v1)
      NO → SARIMA (sarima_daily_v1)
```

