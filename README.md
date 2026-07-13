Here's the cleaned-up summary with filler words removed:

---

Forecasting OON Leakage groups

- Objective: Forecast monthly Network Leakage (Out-of-Network Cost) using a time series model to predict 60 days of Out-of-Network (OON) healthcare costs. The forecast helped Finance and Provider Network teams improve budget planning and proactively manage rising OON expenses.
- Exploratory analysis: Performed EDA to analyze trends, seasonality, outliers, and missing values in OON cost. Time-series decomposition, ADF/KPSS tests for stationarity, and ACF/PACF plots identified lag relationships and temporal behavior for feature engineering.
- Data preparation: Cleaned and aggregated patient claims, provider network data, and member eligibility at the monthly level into a single dataset. Handled missing values, duplicate claims, and outliers. Split data chronologically into training and testing sets to avoid data leakage.
- Feature Engineering: Created lag features, rolling statistics, calendar-based features, and business features (provider count, approximate wait time) to capture historical trends, seasonality, and network conditions while preventing data leakage.
- Model building: Compared baseline ARIMA and SARIMAX with Linear Regression, Random Forest, and XGBoost. Selected XGBoost for superior forecasting accuracy and ability to learn complex business relationships.
- Model Validation: Validated using walk-forward time-series cross-validation to preserve temporal order and prevent data leakage. Optimized hyperparameters and compared performance against baseline models using MAPE (primary), MAE, R2, RMSE.
- Outcome: Generated 60-day OON cost forecasts with XGBoost at 12.6% MAPE. Enabled proactive network gap management, improved budgeting, and reduced future OON cost.

Member Risk Prediction Model

- Objective: Build a machine learning model to identify high-risk Medicare Advantage members likely to incur high healthcare costs or require intensive care management. Help care managers prioritize outreach, improve HCC coding, optimize RAF scores, and support CMS-compliant risk adjustment. Reduce avoidable hospitalizations and improve clinical outcomes through early intervention.
- Exploratory analysis: Analyzed historical claims, eligibility, demographics, pharmacy, and utilization data to understand member health patterns. Identified key risk drivers: chronic conditions, hospitalizations, ER visits, medication usage, and healthcare costs. Assessed missing values, feature correlations, class imbalance, and utilization trends to guide feature engineering and model selection.
- Data preparation: Built a Medallion Architecture on Databricks to ingest, clean, and transform large-scale healthcare datasets. Removed duplicates, handled missing values and outliers, standardized diagnosis/procedure codes, and joined multiple data sources into member-level records. Prevented data leakage. Addressed class imbalance using class weights and balanced sampling.
- Feature Engineering: Engineered features from claims history (diagnosis codes, HCC flags), utilization lag features, clinical features (HCC flags, chronic disease counts, RAF history), inpatient admissions, readmissions, lag features, rolling averages, and cost trends. Added demographic, pharmacy, provider interaction, and temporal features to capture long-term member risk patterns.
- Model building: Trained and compared LightGBM and XGBoost using time-based train-validation splits. Performed hyperparameter tuning with Grid Search/Optuna. Selected LightGBM for best Precision-Recall AUC, faster training, and excellent performance on large, imbalanced healthcare datasets.
- Model Validation: Evaluated using Recall, F1-score, ROC-AUC, PR-AUC, and confusion matrix, with PR-AUC as primary metric due to class imbalance. Used SHAP to explain predictions, identify key risk factors, and improve model transparency. Performed probability calibration and fairness checks across demographic groups.
- Outcome: Achieved 82% recall and 0.91 ROC-AUC, improving high-risk member identification by 18%.

Hospital Readmission Prediction

- Objective: Built a machine learning model to predict 30-day hospital readmission risk, enabling proactive care management and reducing CMS HRRP penalties.
- Exploratory analysis: Analyzed clinical, claims, and demographic data to identify readmission patterns, feature relationships, missing values, and class imbalance.
- Data preparation: Integrated and cleaned multi-source EHR and claims data in Databricks using PySpark, creating leakage-free patient-level datasets.
- Feature Engineering: Engineered clinical, utilization, temporal, and demographic features to capture patient readmission risk.
- Model building: Trained and compared XGBoost and LightGBM models, optimizing for class imbalance and Precision-Recall performance.
- Model Validation: Validated using ROC-AUC, PR-AUC, Recall, F1-score, calibration, fairness analysis, and SHAP explainability.
- Outcome: Achieved 79% recall and 0.88 ROC-AUC, supporting proactive care management and CMS penalty reduction.
