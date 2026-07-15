# Road Accident Severity Prediction

An end-to-end Machine Learning project that predicts road accident severity using historical accident data. The project includes data preprocessing, feature engineering, model training, evaluation, explainability, and will be extended into a full-stack application using FastAPI, React, and MySQL.

---

## Features

- Exploratory Data Analysis (EDA)
- Data Cleaning & Preprocessing
- Feature Engineering
- Multiple Machine Learning Models
- Hyperparameter Tuning
- Model Evaluation
- Explainable Predictions
- FastAPI Backend (In Progress)
- React Frontend (Planned)
- MySQL Database Integration (Planned)

---

## Tech Stack

### Machine Learning

- Python
- NumPy
- Pandas
- Scikit-learn
- XGBoost
- Matplotlib
- Seaborn

### Backend _(Upcoming)_

- FastAPI
- SQLAlchemy
- MySQL

### Frontend _(Upcoming)_

- React
- HTML
- CSS
- JavaScript

---

## Project Structure

```text
Road-Accident-Severity-Prediction/
│
├── notebooks/
├── data/
│   ├── raw/
│   └── processed/
├── models/
├── backend/
├── frontend/
├── images/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Current Progress

- ✅ Exploratory Data Analysis
- ✅ Data Preprocessing
- ✅ Feature Engineering
- ✅ Model Training
- ✅ Hyperparameter Tuning
- ✅ Model Evaluation
- ⏳ FastAPI Backend
- ⏳ MySQL Integration
- ⏳ React Frontend
- ⏳ Deployment

---

## Future Work

- Build a FastAPI backend for model inference.
- Integrate a MySQL database to store prediction history.
- Develop a React frontend for user interaction.
- Deploy the complete application.

---

## Local manual test (backend)

1. Start backend (FastAPI):
   - `uvicorn backend.main:app --reload --port 8000`
2. Check:
   - `GET http://127.0.0.1:8000/health`
   - `GET http://127.0.0.1:8000/docs`
   - `POST http://127.0.0.1:8000/predict`
   - `GET http://127.0.0.1:8000/model-info`

## Local manual test (frontend)

1. Open `frontend/index.html`.
2. Submit the form.
3. Verify the result card shows:
   - Predicted severity
   - Confidence
4. SHAP remains a placeholder (backend currently doesn’t expose SHAP).

---

## Author

**Mallavarapu Sudhishna**
