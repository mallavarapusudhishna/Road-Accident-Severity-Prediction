PRD: AI-Powered Road Accident Risk Prediction System (India)

1. Project Overview

Objective

Build an end-to-end Machine Learning application that predicts road accident risk and severity in India, using a record-level Kaggle accident dataset as the training source. The project should demonstrate a complete ML lifecycle including data engineering, machine learning, API development, frontend development, deployment, and basic MLOps practices.


2. About the Data

Dataset

India Road Accident Dataset – Predictive Analysis (Kaggle, by khushikyad001)
Source: https://www.kaggle.com/datasets/khushikyad001/india-road-accident-dataset-predictive-analysis

This is a record-level (accident-by-accident) dataset covering the years 2018–2023, intended specifically for predictive modeling and risk assessment. Each row represents a single accident with the following attributes:


State and city of occurrence
Year, month, day of week, and exact time (HH:MM) of the accident
Accident severity: Fatal / Serious / Minor
Number of vehicles involved and vehicle type (Car, Truck, Two-Wheeler, etc.)
Driver age, gender, and license status
Weather condition, lighting condition, road type, and speed limit at the accident location
Alcohol involvement (drunk driving flag)


This dataset supplies the record-level features needed to train a per-accident risk/severity model.


3. Problem Statement

Road accident data is often analyzed only in hindsight through static reports.

The objective is to build a unified system that:


Cleans and prepares accident-level data
Generates meaningful features
Trains ML models
Predicts accident risk/severity
Provides interactive visualizations



4. Technology Stack

LayerChoiceFrontendReact (or HTML/CSS/JS)BackendFastAPIDatabasePostgreSQL (or MySQL)MLPandas, NumPy, Scikit-learn, XGBoost, LightGBM (optional)VisualizationPlotly, Chart.js, RechartsDeploymentDocker, AWS EC2, Nginx, GitHub Actions


5. System Architecture

Kaggle Dataset
      |
      v
 Data Cleaning
      |
      v
Feature Engineering
      |
      v
  PostgreSQL
      |
   ---------
   |       |
   v       v
ML Training   FastAPI
   |            |
   v            v
Model File   Prediction API
                |
                v
          React Dashboard
                |
                v
          AWS Deployment


6. Data Sources

India Road Accident Dataset – Predictive Analysis (Kaggle, khushikyad001), 2018–2023:

state, city, year, month, day_of_week, time, severity, num_vehicles, vehicle_type,
driver_age, driver_gender, license_status, weather, lighting, road_type, speed_limit,
alcohol_involved


7. ML Pipeline

Collect Data → Clean Data → EDA →
Feature Engineering → Train/Test Split → Train Models →
Evaluate → Save Best Model → Deploy

Target variable: Accident severity (Fatal / Serious / Minor) — framed as a classification problem.

Models to implement and compare: Logistic Regression, Random Forest, XGBoost. Select best model based on evaluation metrics.


8. API Endpoints

MethodEndpointPurposePOST/uploadUpload datasetPOST/predictReturn prediction based on user inputs (state, year, month, day of week, time, vehicle type, driver age/gender, weather, lighting, road type, speed limit, alcohol involvement)GET/statisticsReturn dashboard statisticsGET/model-infoReturn model information and evaluation metrics


9. Database Schema

accidents (record-level, from Kaggle dataset)

id, state, city, year, month, day_of_week, time,
severity, num_vehicles, vehicle_type,
driver_age, driver_gender, license_status,
weather, lighting, road_type, speed_limit,
alcohol_involved

predictions

id, state, prediction, created_at


10. Folder Structure

road-accident-ml/
|
├── data/
├── notebooks/
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── database/
├── frontend/
├── ml/
│   ├── training/
│   ├── preprocessing/
│   └── inference/
├── docker/
└── README.md


11. MLOps Workflow

GitHub → GitHub Actions → Run Tests →
Train Model (Manual/Triggered) → Store Model Artifact →
Docker Build → Deploy to AWS EC2 → Serve Predictions via FastAPI