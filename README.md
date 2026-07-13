1. Objective

Developed a time series forecasting model to predict 60 days of Out-of-Network (OON) healthcare costs. The forecast helped Finance and Provider Network teams improve budget planning and proactively manage rising OON expenses.

2. Exploratory Data Analysis (EDA)

Performed data quality checks, trend analysis, and visualized seasonality using rolling statistics and STL decomposition. Conducted the ADF test to verify stationarity before model building.

3. Data Preparation

Handled missing values, duplicates, and outliers, then aggregated claims into a daily time series. Split the data chronologically into training and testing sets to avoid data leakage.

4. Feature Engineering

Created lag, rolling average, calendar, and business features such as claim count and holiday indicators. These features captured historical patterns and improved forecasting performance.

5. Model Building

Built and compared SARIMA, SARIMAX, and XGBoost models using historical and business features. Selected the best-performing model based on forecasting accuracy.

6. Model Validation

Evaluated models using MAE, RMSE, and MAPE on a time-based test set. Compared baseline and advanced models to ensure reliable predictions.

7. Outcome

Generated accurate 60-day OON cost forecasts that supported budgeting and early identification of rising healthcare costs. The solution enabled more proactive financial and operational decision-making.
