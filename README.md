# Road Accident Severity Prediction System

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7+-blue.svg)](https://xgboost.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 1. Overview

The Road Accident Severity Prediction System is an end-to-end machine learning pipeline and web application designed to forecast the severity of traffic collisions. By leveraging historical accident data and real-time environmental inputs, the system provides actionable intelligence for emergency response dispatchers, traffic management authorities, and urban planners. 

The primary objective is to facilitate proactive resource allocation and improve road safety measures through data-driven insights and explainable artificial intelligence (XAI).

## 2. System Architecture

The application is built upon a unified, decoupled architecture prioritizing high throughput and maintainability:

*   **Inference Engine (Backend):** Developed using FastAPI, the backend exposes RESTful endpoints for real-time model inference. It handles strict data validation, interacts with the loaded XGBoost model, and computes SHAP (SHapley Additive exPlanations) values for prediction interpretability.
*   **Presentation Layer (Frontend):** A responsive, single-page application built with HTML5, CSS3, and ES6 JavaScript. The frontend is served directly via FastAPI's static file mounting, eliminating the need for a separate web server.
*   **Persistence Layer:** SQLAlchemy ORM is utilized for logging prediction metadata, confidence scores, and input parameters. The system defaults to SQLite for localized development and seamlessly scales to PostgreSQL for production environments.

## 3. Core Capabilities

*   **Real-time Inference:** Sub-millisecond prediction latency using optimized tree-based models (XGBoost).
*   **Model Interpretability:** On-the-fly feature importance generation (SHAP), ensuring that all predictions remain transparent and auditable.
*   **Comprehensive Data Validation:** Robust backend validation logic to prevent erroneous or maliciously formatted input data from reaching the inference engine.
*   **Historical Analytics:** Integrated endpoints for aggregating and analyzing past predictions to identify long-term spatial and temporal accident trends.

## 4. Technical Stack

*   **Machine Learning:** Python, Pandas, NumPy, Scikit-learn, XGBoost, SHAP
*   **Backend Framework:** FastAPI, Uvicorn, Pydantic
*   **Database:** SQLAlchemy, SQLite / PostgreSQL
*   **Frontend Technologies:** HTML, CSS, JavaScript (Vanilla ES6+)

## 5. Getting Started

### 5.1. Prerequisites

Ensure the following dependencies are installed on the host machine:
*   Python (>= 3.9)
*   pip (Python package installer)

### 5.2. Local Installation

1.  Clone the repository to your local environment.
2.  Navigate to the project root directory.
3.  Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5.3. Starting the Server

The application server can be initialized using `uvicorn`. From the root directory, execute:

```bash
uvicorn backend.main:app --reload
```

The unified server will mount both the API endpoints and the static frontend assets on port 8000.

### 5.4. Accessing the Interfaces

*   **Web Dashboard:** `http://localhost:8000/`
*   **OpenAPI Interactive Documentation (Swagger UI):** `http://localhost:8000/docs`
*   **API Health Check:** `http://localhost:8000/health`

## 6. Usage

1.  Access the Web Dashboard via a standard web browser.
2.  Input the contextual parameters of the incident (e.g., temporal data, weather conditions, lighting, and road surface state).
3.  Submit the payload to generate a prediction.
4.  The system will return the classified severity level (Minor, Serious, or Fatal), the associated statistical confidence, and an underlying probability distribution.

## 7. Roadmap

*   **Containerization:** Implementation of Dockerfiles and docker-compose configurations for isolated, reproducible deployments.
*   **Geospatial Integration:** Enhancing the frontend dashboard with GIS mapping capabilities for spatial cluster analysis.
*   **Continuous Integration (CI/CD):** Establishing automated test suites and deployment pipelines using GitHub Actions.

## 8. Author

**Sudhishna Mallavarapu**
