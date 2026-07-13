# Road Accident Severity Predictor (Frontend)

Vanilla JS + HTML frontend for predicting road accident severity.

## Files

- `index.html` – UI (form + result)
- `app.js` – calls backend + local caching
- `styles.css` – styling

## Configure backend URL

This frontend expects the FastAPI backend to expose:

- `POST /predict`

By default `app.js` uses:

- `http://127.0.0.1:8000/predict`

To change it:

- Edit the `API_BASE` constant in `app.js`, **or**
- Serve the page with `window.API_BASE` defined.

## Run locally (simplest)

Because it uses `fetch()`, you can open the file in a browser. If your browser blocks requests due to CORS, run backend with permissive CORS (it already has `allow_origins=["*"]`).

1. Start backend server (FastAPI)
2. Open:
   - `frontend/index.html`

## SHAP explanation

Backend currently returns only:

- `predicted_severity`
- `confidence`

The SHAP section in the UI is a placeholder until backend exposes SHAP values/plots.
