Here are concise summaries for all three projects:

---

1. Forecasting OON Leakage Groups

Objective
Forecast monthly Out-of-Network (OON) healthcare costs 60 days ahead to improve budget planning and proactively manage rising OON expenses.

Data Source and Preparation
Merged patient claims, provider network data, and member eligibility into monthly aggregates. Handled missing values, duplicates, and outliers. Split data chronologically to prevent leakage.

Model Building and Output
Compared ARIMA, SARIMAX, Linear Regression, Random Forest, and XGBoost. Selected XGBoost for superior accuracy and ability to learn complex business relationships. Validated via walk-forward time-series cross-validation with hyperparameter optimization. Primary metric: MAPE (also MAE, R², RMSE).

Business Impact
Generated 60-day OON cost forecasts at 12.6% MAPE. Enabled proactive network gap management, improved budgeting, and reduced future OON costs.

---

2. Member Risk Prediction Model

Objective
Identify high-risk Medicare Advantage members likely to incur high healthcare costs or need intensive care management. Support care manager prioritization, HCC coding, RAF score optimization, and CMS-compliant risk adjustment to reduce avoidable hospitalizations.

Data Source and Preparation
Built Medallion Architecture on Databricks to ingest, clean, and transform large-scale healthcare datasets. Standardized diagnosis/procedure codes, joined multiple sources into member-level records. Addressed class imbalance via class weights and balanced sampling.

Model Building and Output
Trained LightGBM and XGBoost with time-based train-validation splits. Hyperparameter tuning via Grid Search/Optuna. Selected LightGBM for best Precision-Recall AUC, faster training, and performance on imbalanced data. Evaluated using Recall, F1-score, ROC-AUC, PR-AUC (primary), and confusion matrix. SHAP used for explainability; probability calibration and fairness checks performed across demographic groups.

Business Impact
Achieved 82% recall and 0.91 ROC-AUC, improving high-risk member identification by 18%.

---

3. Hospital Readmission Prediction

Objective
Predict 30-day hospital readmission risk to enable proactive care management and reduce CMS HRRP penalties.

Data Source and Preparation
Integrated and cleaned multi-source EHR and claims data in Databricks using PySpark. Created leakage-free, patient-level datasets.

Model Building and Output
Engineered clinical, utilization, temporal, and demographic features. Trained and compared XGBoost and LightGBM, optimizing for class imbalance and Precision-Recall performance. Validated using ROC-AUC, PR-AUC, Recall, F1-score, calibration, fairness analysis, and SHAP explainability.

Business Impact
Achieved 79% recall and 0.88 ROC-AUC, supporting proactive care management and CMS penalty reduction.
