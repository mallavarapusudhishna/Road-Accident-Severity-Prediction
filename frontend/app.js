const API_BASE = window.API_BASE || "http://127.0.0.1:8000";

const form = document.getElementById("predict-form");
const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const clearBtn = document.getElementById("clear-btn");

const predictedSeverityEl = document.getElementById("predicted-severity");
const confidenceEl = document.getElementById("confidence");

const shapNoteEl = document.getElementById("shap-note");

function normalizeValue(v) {
  if (v === null || v === undefined) return "";
  return String(v).trim();
}

function buildPayloadFromForm(fd) {
  const payload = {};

  // Required by backend PredictionRequest
  payload.state = normalizeValue(fd.get("state"));
  payload.city = normalizeValue(fd.get("city")) || "Unknown";
  payload.year = Number(normalizeValue(fd.get("year")));
  payload.month = normalizeValue(fd.get("month"));
  payload.day_of_week = normalizeValue(fd.get("day_of_week"));
  payload.time = normalizeValue(fd.get("time"));

  // Inputs present on the reduced form
  payload.num_vehicles = 1; // default: user not asked
  payload.vehicle_type = normalizeValue(fd.get("vehicle_type"));
  payload.weather = "Clear"; // default: user not asked
  payload.road_type = normalizeValue(fd.get("road_type")) || "Urban"; // if not present, default below

  // If road_type input is not in the reduced form, use default
  if (!payload.road_type) payload.road_type = "Urban";

  payload.road_condition = "Under Construction"; // default
  payload.lighting_conditions = "Dark"; // default
  payload.traffic_control_presence = "Signs"; // default

  payload.speed_limit_kmh = Number(normalizeValue(fd.get("speed_limit_kmh")));
  payload.driver_age = Number(normalizeValue(fd.get("driver_age")));
  payload.driver_gender = "Male"; // default
  payload.driver_license_status = null; // not asked

  payload.alcohol_involved = normalizeValue(fd.get("alcohol_involved"));
  payload.accident_location_details = "Intersection"; // default

  return payload;
}

function stableStringify(obj) {
  if (obj === null || obj === undefined) return "";
  const keys = Object.keys(obj).sort();
  const out = {};
  for (const k of keys) out[k] = obj[k];
  return JSON.stringify(out);
}

function cacheKeyForPayload(payload) {
  // Cache in localStorage so repeat queries are instant.
  return "prediction_cache_v1_" + stableStringify(payload);
}

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.className = isError ? "status error" : "status";
}

function renderPrediction(prediction) {
  const card = document.getElementById("result-card");
  if (card) {
    card.classList.remove("is-hidden");
    card.classList.add("is-visible");
  }
  resultEl.style.display = "block";

  predictedSeverityEl.textContent = prediction.predicted_severity;
  confidenceEl.textContent =
    typeof prediction.confidence === "number"
      ? prediction.confidence.toFixed(3)
      : String(prediction.confidence);

  // Backend currently returns only severity + confidence.
  // Reason-of-accident (SHAP) integration will be added once backend exposes SHAP values.
  shapNoteEl.textContent =
    "Reason-of-accident (SHAP) is not available yet from the backend.";

  const shapContent = document.getElementById("shap-content");
  if (shapContent) {
    shapContent.textContent =
      "Run prediction again after SHAP endpoint is added to backend.";
  }
}

async function callBackendPredict(payload) {
  // Ensure payload is exactly what backend expects (no undefined keys)
  const res = await fetch(API_BASE + "/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error (${res.status}): ${text || res.statusText}`);
  }
  return res.json();
}

// Hide result while user types/edits inputs (so it never shows during typing).
Array.from(form.querySelectorAll("input, select, textarea")).forEach(el => {
  el.addEventListener("input", () => {
    resultEl.style.display = "none";
    const card = document.getElementById("result-card");
    if (card) {
      card.classList.remove("is-visible");
      card.classList.add("is-hidden");
    }
    resultEl.setAttribute("aria-hidden", "true");

    // Keep status as-is (optional). If you want it cleared, uncomment next line.

    // statusEl.textContent = "";
  });
});

form.addEventListener("submit", async e => {
  e.preventDefault();

  // Hide previous result immediately when user clicks Predict.
  resultEl.style.display = "none";
  resultEl.setAttribute("aria-hidden", "true");
  const card = document.getElementById("result-card");
  if (card) {
    card.classList.remove("is-visible");
    card.classList.add("is-hidden");
  }

  setStatus("Predicting...");

  try {
    const fd = new FormData(form);
    const payload = buildPayloadFromForm(fd);
    const key = cacheKeyForPayload(payload);

    const cached = localStorage.getItem(key);
    if (cached) {
      setStatus("Loaded from local cache.");
      renderPrediction(JSON.parse(cached));
      return;
    }

    const prediction = await callBackendPredict(payload);
    localStorage.setItem(key, JSON.stringify(prediction));
    setStatus("Prediction complete.");
    renderPrediction(prediction);
  } catch (err) {
    console.error(err);
    setStatus(String(err.message || err), true);
  }
});

clearBtn.addEventListener("click", () => {
  form.reset();
  resultEl.style.display = "none";
  const card = document.getElementById("result-card");
  if (card) {
    card.classList.remove("is-visible");
    card.classList.add("is-hidden");
  }
  statusEl.textContent = "";
});
