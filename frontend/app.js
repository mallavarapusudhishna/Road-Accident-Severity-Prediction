const API_BASE = window.API_BASE || "";

// Stepper Navigation Elements
const form = document.getElementById("predict-form");
const steps = Array.from(document.querySelectorAll(".wizard-step"));
const stepIndicators = Array.from(document.querySelectorAll(".step-indicator"));
const nextBtn = document.getElementById("next-btn");
const prevBtn = document.getElementById("prev-btn");
const predictBtn = document.getElementById("predict-btn");
const clearBtn = document.getElementById("clear-btn");

// Single-page form: if wizard controls are missing, disable step validation.
const isSinglePage = steps.length === 0;

// Input Badges / Indicators
const speedLimitInput = document.getElementById("speed_limit_kmh");
const speedLimitBadge = document.getElementById("speed-limit-badge");
const driverAgeInput = document.getElementById("driver_age");
const driverAgeBadge = document.getElementById("driver-age-badge");
const alcoholCheck = document.getElementById("alcohol_involved_check");
const alcoholLabel = document.getElementById("alcohol-label");

// Results Panel Elements
const loaderCard = document.getElementById("loader-card");
const resultCard = document.getElementById("result-card");
const riskBadge = document.getElementById("risk-badge");
const resultHeading = document.getElementById("result-heading");
const confidencePercentage = document.getElementById("confidence-percentage");
const confidenceBar = document.getElementById("confidence-bar");

const probFillFatal = document.getElementById("prob-fill-fatal");
const probValFatal = document.getElementById("prob-val-fatal");
const probFillSerious = document.getElementById("prob-fill-serious");
const probValSerious = document.getElementById("prob-val-serious");
const probFillMinor = document.getElementById("prob-fill-minor");
const probValMinor = document.getElementById("prob-val-minor");

const shapBarContainer = document.getElementById("shap-bar-container");
const shapExplanation = document.getElementById("shap-explanation");
const predictionTimestamp = document.getElementById("prediction-timestamp");

let currentStep = 1;

// 1. INITIALIZE DASHBOARD STATISTICS ON PAGE LOAD
async function initDashboardStats() {
  try {
    const res = await fetch(`${API_BASE}/statistics`);
    if (!res.ok) throw new Error("Could not retrieve statistics");
    const stats = await res.json();

    // Set total records counter
    const recordsEl = document.getElementById("stats-total-records");
    if (recordsEl) {
      recordsEl.textContent = Number(stats.records).toLocaleString();
    }

    // Set severity distribution ratio bars
    const dist = stats.severity_distribution || {};
    const total = (dist.Minor || 0) + (dist.Serious || 0) + (dist.Fatal || 0);

    if (total > 0) {
      const minorPct = (((dist.Minor || 0) / total) * 100).toFixed(1);
      const seriousPct = (((dist.Serious || 0) / total) * 100).toFixed(1);
      const fatalPct = (((dist.Fatal || 0) / total) * 100).toFixed(1);

      const minorBar = document.getElementById("dist-bar-minor");
      const seriousBar = document.getElementById("dist-bar-serious");
      const fatalBar = document.getElementById("dist-bar-fatal");

      if (minorBar) {
        minorBar.style.width = `${minorPct}%`;
        minorBar.querySelector("span").textContent = `Minor: ${minorPct}%`;
      }
      if (seriousBar) {
        seriousBar.style.width = `${seriousPct}%`;
        seriousBar.querySelector("span").textContent =
          `Serious: ${seriousPct}%`;
      }
      if (fatalBar) {
        fatalBar.style.width = `${fatalPct}%`;
        fatalBar.querySelector("span").textContent = `Fatal: ${fatalPct}%`;
      }
    }
  } catch (err) {
    console.warn("Failed to load statistics dashboard:", err);
  }
}

// 2. FORM STEPPER NAVIGATION (disabled for single-page redesign)
// Get the visible element associated with a form input
function getVisibleInputEl(field) {
  if (field.classList.contains("sdd-native-hidden")) {
    const root = field.previousElementSibling;
    if (root && root.classList.contains("sdd-root")) {
      return root.querySelector(".sdd-trigger");
    }
  }
  return field;
}

// Display error highlight and message directly below the field
function showFieldError(field, message) {
  const visibleEl = getVisibleInputEl(field);
  visibleEl.classList.add("validation-error");

  const formGroup = field.closest(".form-group");
  if (formGroup) {
    let msgEl = formGroup.querySelector(".validation-msg");
    if (!msgEl) {
      msgEl = document.createElement("span");
      msgEl.className = "validation-msg";
      msgEl.textContent = message;
      formGroup.appendChild(msgEl);
    }
  }
}

// Clear error highlight and message
function clearFieldError(field) {
  const visibleEl = getVisibleInputEl(field);
  visibleEl.classList.remove("validation-error");

  const formGroup = field.closest(".form-group");
  if (formGroup) {
    const msgEl = formGroup.querySelector(".validation-msg");
    if (msgEl) {
      msgEl.remove();
    }
  }
}

const FIELD_ERROR_MESSAGES = {
  "state": "Please select a state.",
  "accident-date": "Please select the accident date.",
  "accident-time": "Please select the accident time.",
  "num_vehicles": "Please enter the number of vehicles.",
  "road_type": "Please select a road type.",
  "accident_location_details": "Please select a road layout.",
  "road_condition": "Please select a road condition.",
  "weather": "Please select a weather condition.",
  "lighting_conditions": "Please select a lighting condition.",
  "traffic_control_presence": "Please select a traffic control.",
  "vehicle_type": "Please select a vehicle type.",
  "driver_license_status": "Please select a license status."
};

function getErrorMessageForField(field) {
  const idOrName = field.id || field.name;
  return FIELD_ERROR_MESSAGES[idOrName] || "Please answer this question.";
}

// Custom validation function
function validateForm() {
  const requiredFields = Array.from(form.querySelectorAll("[required]"));
  
  for (const field of requiredFields) {
    const val = field.value;
    if (!val || !String(val).trim()) {
      // Show error on the FIRST unanswered question only
      const errorMsg = getErrorMessageForField(field);
      showFieldError(field, errorMsg);
      
      const visibleEl = getVisibleInputEl(field);
      visibleEl.scrollIntoView({ behavior: "smooth", block: "center" });
      visibleEl.focus();
      return false;
    } else {
      clearFieldError(field);
    }
  }
  return true;
}

// Setup validation listeners to clear errors immediately on user input/change
function setupValidationListeners() {
  const requiredFields = form.querySelectorAll("[required]");
  requiredFields.forEach(field => {
    const handleInput = () => {
      if (field.value && String(field.value).trim()) {
        clearFieldError(field);
      }
    };
    field.addEventListener("input", handleInput);
    field.addEventListener("change", handleInput);
  });
}

function validateCurrentStep() {
  return validateForm();
}

function updateStepperUI() {
  if (isSinglePage) return;

  steps.forEach((step, idx) => {
    step.classList.toggle("active", idx === currentStep - 1);
  });

  stepIndicators.forEach((indicator, idx) => {
    indicator.classList.toggle("active", idx === currentStep - 1);
  });

  if (currentStep === 1) {
    prevBtn?.classList.add("is-hidden");
    nextBtn?.classList.remove("is-hidden");
    predictBtn?.classList.add("is-hidden");
  } else if (currentStep === 2) {
    prevBtn?.classList.remove("is-hidden");
    nextBtn?.classList.remove("is-hidden");
    predictBtn?.classList.add("is-hidden");
  } else if (currentStep === 3) {
    prevBtn?.classList.remove("is-hidden");
    nextBtn?.classList.add("is-hidden");
    predictBtn?.classList.remove("is-hidden");
  }
}

// Hook stepper buttons only if they exist (prevents single-page crashes)
if (nextBtn) {
  nextBtn.addEventListener("click", () => {
    if (!isSinglePage && validateCurrentStep()) {
      currentStep++;
      updateStepperUI();
    }
  });
}

if (prevBtn) {
  prevBtn.addEventListener("click", () => {
    if (!isSinglePage) {
      currentStep--;
      updateStepperUI();
    }
  });
}

// 3. UI FORM COMPONENT LISTENERS
function updateSpeedUI(value) {
  if (speedLimitBadge) speedLimitBadge.textContent = value;
  const tooltipValue = document.getElementById("speed-limit-tooltip-value");
  const tooltip = document.getElementById("speed-limit-tooltip");
  if (tooltipValue) tooltipValue.textContent = value;
  if (tooltip && speedLimitInput) {
    const min = Number(speedLimitInput.min || 30);
    const max = Number(speedLimitInput.max || 120);
    const pct = max === min ? 0 : ((Number(value) - min) / (max - min)) * 100;
    tooltip.style.left = `calc(${pct}% + 0px)`;
  }
}

function updateAgeUI(value) {
  if (driverAgeBadge) driverAgeBadge.textContent = String(value);
  const tooltip = document.getElementById("driver-age-tooltip");
  const tooltipValue = document.getElementById("driver-age-tooltip-value");

  if (!tooltip) return;
  if (!tooltipValue) {
    tooltip.textContent = String(value);
  } else {
    tooltipValue.textContent = String(value);
  }

  if (driverAgeInput) {
    // Move tooltip based on range position
    const min = Number(driverAgeInput.min || 0);
    const max = Number(driverAgeInput.max || 100);
    const pct = max === min ? 0 : ((Number(value) - min) / (max - min)) * 100;
    tooltip.style.left = `calc(${pct}% + 0px)`;
  }
}

if (speedLimitInput) {
  const tooltip = document.getElementById("speed-limit-tooltip");

  speedLimitInput.addEventListener("input", e => {
    updateSpeedUI(e.target.value);
    if (tooltip) tooltip.hidden = false;
  });

  speedLimitInput.addEventListener("mousedown", () => {
    if (tooltip) tooltip.hidden = false;
  });
  speedLimitInput.addEventListener("mouseup", () => {
    if (tooltip) tooltip.hidden = true;
  });
  speedLimitInput.addEventListener("touchend", () => {
    if (tooltip) tooltip.hidden = true;
  });

  updateSpeedUI(speedLimitInput.value);
}

if (driverAgeInput) {
  const tooltip = document.getElementById("driver-age-tooltip");

  driverAgeInput.addEventListener("input", e => {
    updateAgeUI(e.target.value);
    if (tooltip) tooltip.hidden = false;
  });

  driverAgeInput.addEventListener("mousedown", () => {
    if (tooltip) tooltip.hidden = false;
  });

  // Hide tooltip when dragging ends
  driverAgeInput.addEventListener("mouseup", () => {
    if (tooltip) tooltip.hidden = true;
  });
  driverAgeInput.addEventListener("touchend", () => {
    if (tooltip) tooltip.hidden = true;
  });

  // Initialize
  updateAgeUI(driverAgeInput.value);
}

if (alcoholCheck) {
  alcoholCheck.addEventListener("change", e => {
    alcoholLabel.textContent = e.target.checked ? "Yes" : "No";
  });
}



// Reset results fields on clear / page load
function resetResultsUI() {
  if (riskBadge) riskBadge.textContent = "—";
  if (resultHeading) resultHeading.textContent = "—";
  if (confidencePercentage) confidencePercentage.textContent = "0%";
  if (confidenceBar) confidenceBar.style.strokeDasharray = "0, 100";

  if (probFillFatal) probFillFatal.style.width = "0%";
  if (probValFatal) probValFatal.textContent = "0%";
  if (probFillSerious) probFillSerious.style.width = "0%";
  if (probValSerious) probValSerious.textContent = "0%";
  if (probFillMinor) probFillMinor.style.width = "0%";
  if (probValMinor) probValMinor.textContent = "0%";

  if (shapBarContainer) shapBarContainer.innerHTML = "";
  if (shapExplanation) shapExplanation.textContent = "";
  if (predictionTimestamp) predictionTimestamp.textContent = "—";
}

// Reset page session and setup picker behaviors on load
window.addEventListener("DOMContentLoaded", () => {
  // 1. Reset form and results UI completely to start a new clean session
  if (form) form.reset();
  resetResultsUI();

  // 2. Clear all validation styles
  const requiredFields = form.querySelectorAll("[required]");
  requiredFields.forEach(clearFieldError);

  // 3. Initialize date/time pickers with custom dynamic type-switching
  // (inputs are now native date/time — no setup needed)

  // 4. Setup change/input validators to remove red highlights immediately when answered
  setupValidationListeners();

  // 5. Sync sliders tooltips
  if (speedLimitInput) {
    updateSpeedUI(speedLimitInput.value);
  }
  if (driverAgeInput) {
    updateAgeUI(driverAgeInput.value);
  }
  if (alcoholLabel) {
    alcoholLabel.textContent = "No";
  }

  // 6. Load stats dashboard counters
  initDashboardStats();
});

// 4. PARSE DATE PICKER DETAILS
function parseDateDetails(dateStr) {
  const dt = new Date(dateStr);
  if (isNaN(dt.getTime())) {
    throw new Error("Invalid date string provided.");
  }
  const year = dt.getFullYear();

  const monthNames = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
  ];
  const month = monthNames[dt.getMonth()];

  const dayNames = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];
  const day_of_week = dayNames[dt.getDay()];

  return { year, month, day_of_week };
}

// 5. CACHING HELPERS
const CACHE_PREFIX = "prediction_cache_v3_";
const MAX_CACHE_ENTRIES = 50;

function stableStringify(obj) {
  if (!obj) return "";
  const keys = Object.keys(obj).sort();
  const out = {};
  for (const k of keys) out[k] = obj[k];
  return JSON.stringify(out);
}

function cacheKeyForPayload(payload) {
  return CACHE_PREFIX + stableStringify(payload);
}

function manageCacheSize() {
  const keys = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith(CACHE_PREFIX)) {
      keys.push(key);
    }
  }
  if (keys.length > MAX_CACHE_ENTRIES) {
    for (let i = 0; i < keys.length - MAX_CACHE_ENTRIES; i++) {
      localStorage.removeItem(keys[i]);
    }
  }
}

// 6. SUBMIT & PREDICT HANDLER
form.addEventListener("submit", async e => {
  e.preventDefault();

  if (!validateForm()) return;

  // Retrieve inputs
  const state = document.getElementById("state").value;
  const dateStr = document.getElementById("accident-date").value;
  const timeStr = document.getElementById("accident-time").value;
  const num_vehicles = parseInt(
    document.getElementById("num_vehicles").value,
    10,
  );
  const road_type = document.getElementById("road_type").value;
  const accident_location_details = document.getElementById(
    "accident_location_details",
  ).value;
  const road_condition = document.getElementById("road_condition").value;
  const weather = document.getElementById("weather").value;
  const lighting_conditions = document.getElementById(
    "lighting_conditions",
  ).value;
  const traffic_control_presence = document.getElementById(
    "traffic_control_presence",
  ).value;
  const vehicle_type = document.getElementById("vehicle_type").value;
  const speed_limit_kmh = parseInt(speedLimitInput.value, 10);
  const driver_age = parseInt(driverAgeInput.value, 10);
  const driver_license_status = document.getElementById(
    "driver_license_status",
  ).value;
  const alcohol_involved = alcoholCheck.checked ? "Yes" : "No";

  const { year, month, day_of_week } = parseDateDetails(dateStr);

  // Construct payload matching FastAPI PredictionRequest
  const payload = {
    state,
    city: "Unknown",
    year,
    month,
    day_of_week,
    time: timeStr,
    num_vehicles,
    vehicle_type,
    weather,
    road_type,
    road_condition,
    lighting_conditions,
    traffic_control_presence,
    speed_limit_kmh,
    driver_age,
    driver_gender: "Male",
    driver_license_status,
    alcohol_involved,
    accident_location_details,
  };

  // Hide previous result and show loading state
  resultCard.classList.add("is-hidden");
  loaderCard.classList.remove("is-hidden");
  setButtonsDisabled(true);

  // Scroll to the loader card immediately so the user isn't waiting on a blank screen
  loaderCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

  try {
    const key = cacheKeyForPayload(payload);
    const cached = localStorage.getItem(key);

    if (cached) {
      // Artificial delay to make loading look fluid and professional
      await new Promise(resolve => setTimeout(resolve, 600));
      const res = JSON.parse(cached);
      renderPrediction(res);
      // Reload stats dashboard since record was simulated
      initDashboardStats();
      return;
    }

    const res = await callBackendPredict(payload);
    localStorage.setItem(key, JSON.stringify(res));
    manageCacheSize();
    renderPrediction(res);
    // Reload stats dashboard
    initDashboardStats();
  } catch (err) {
    console.error(err);
    // Display validation errors as a readable list
    if (err.validationErrors && err.validationErrors.length > 0) {
      const messages = err.validationErrors.map(e => `• ${e}`).join("\n");
      alert(`Validation Error:\n\n${messages}`);
    } else {
      alert(`Prediction Error: ${err.message || err}`);
    }
    loaderCard.classList.add("is-hidden");
  } finally {
    setButtonsDisabled(false);
  }
});

async function callBackendPredict(payload) {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    // Try to parse structured validation errors from the backend
    let errorBody;
    try {
      errorBody = await res.json();
    } catch {
      const text = await res.text().catch(() => "");
      throw new Error(`API error (${res.status}): ${text || res.statusText}`);
    }

    // Backend sends {detail: {detail: "...", validation_errors: [...]}} for 422
    const detail = errorBody?.detail;
    if (detail && typeof detail === "object" && Array.isArray(detail.validation_errors)) {
      const err = new Error(detail.detail || "Validation failed");
      err.validationErrors = detail.validation_errors;
      throw err;
    }

    // Pydantic validation errors (field-level)
    if (Array.isArray(errorBody?.detail)) {
      const msgs = errorBody.detail.map(d => d.msg || JSON.stringify(d));
      const err = new Error("Input validation failed");
      err.validationErrors = msgs;
      throw err;
    }

    throw new Error(`API error (${res.status}): ${JSON.stringify(errorBody)}`);
  }
  return res.json();
}

function setButtonsDisabled(disabled) {
  if (predictBtn) predictBtn.disabled = disabled;
  if (prevBtn) prevBtn.disabled = disabled;
  if (clearBtn) clearBtn.disabled = disabled;
  if (nextBtn) nextBtn.disabled = disabled; // also disable next button if present
}

// 7. RENDER RESULTS PANEL
function getFriendlyFeatureName(rawName) {
  // Convert encoded one-hot/derived feature names into recruiter-friendly labels.
  if (rawName.startsWith("state_"))
    return `📍 ${rawName.replace("state_", "")}`;
  if (rawName.startsWith("weather_"))
    return `🌦️ ${rawName.replace("weather_", "")}`;
  if (rawName.startsWith("road_type_"))
    return `🛣️ ${rawName.replace("road_type_", "")}`;
  if (rawName.startsWith("road_condition_"))
    return `🏞️ ${rawName.replace("road_condition_", "")}`;
  if (rawName.startsWith("lighting_conditions_"))
    return `💡 ${rawName.replace("lighting_conditions_", "")}`;
  if (rawName.startsWith("traffic_control_presence_")) {
    const val = rawName.replace("traffic_control_presence_", "");
    return `🚦 ${val === "nan" ? "Unknown" : val}`;
  }
  if (rawName.startsWith("vehicle_type_"))
    return `🚗 ${rawName.replace("vehicle_type_", "")}`;
  if (rawName.startsWith("driver_license_status_"))
    return `📜 ${rawName.replace("driver_license_status_", "")}`;
  if (rawName.startsWith("alcohol_involved_"))
    return `🍺 ${rawName.replace("alcohol_involved_", "")}`;
  if (rawName.startsWith("accident_location_details_"))
    return `🧭 ${rawName.replace("accident_location_details_", "")}`;
  if (rawName.startsWith("time_of_day_"))
    return `🌙 ${rawName.replace("time_of_day_", "")}`;
  if (rawName.startsWith("driver_age_group_"))
    return `👤 ${rawName.replace("driver_age_group_", "")}`;

  if (rawName.startsWith("is_night_"))
    return rawName.endsWith("Yes")
      ? "🌙 Poor visibility (Night)"
      : "☀️ Daytime";
  if (rawName.startsWith("is_weekend_"))
    return rawName.endsWith("Yes") ? "📅 Weekend" : "📅 Weekday";
  if (rawName.startsWith("is_peak_hour_"))
    return rawName.endsWith("Yes")
      ? "🚦 Peak traffic hour"
      : "🛑 Off-peak hour";
  if (rawName.startsWith("is_multi_vehicle_"))
    return rawName.endsWith("Yes")
      ? "🚚 Multiple vehicles"
      : "🚗 Single vehicle";

  if (rawName === "speed_limit_(km/h)" || rawName === "speed_limit_kmh")
    return "⚡ Speed limit";
  if (rawName === "driver_age") return "👤 Driver age";
  if (rawName === "num_vehicles") return "🚚 Vehicles involved";
  if (rawName === "year") return "🗓️ Accident year";
  if (rawName.startsWith("day_of_week_"))
    return `📆 ${rawName.replace("day_of_week_", "")}`;
  if (rawName.startsWith("month_"))
    return `📅 ${rawName.replace("month_", "")}`;

  return rawName.replace(/_/g, " ");
}

function renderPrediction(res) {
  loaderCard.classList.add("is-hidden");
  resultCard.classList.remove("is-hidden");

  // Determine Class styling
  const severity = res.predicted_severity;
  resultCard.className = "card result-card"; // Reset

  if (severity === "Fatal") {
    resultCard.classList.add("risk-high");
    riskBadge.textContent = "Fatal Risk";
    resultHeading.textContent = "High Fatality Risk";
  } else if (severity === "Serious") {
    resultCard.classList.add("risk-medium");
    riskBadge.textContent = "Serious Injury";
    resultHeading.textContent = "Medium Severity Risk";
  } else {
    resultCard.classList.add("risk-low");
    riskBadge.textContent = "Minor Injury";
    resultHeading.textContent = "Low Severity Risk";
  }

  // Set Confidence radial gauge
  const confidencePercent = (res.confidence * 100).toFixed(1);
  confidencePercentage.textContent = `${confidencePercent}%`;
  // Radial dasharray mapping 0-100
  confidenceBar.style.strokeDasharray = `${confidencePercent}, 100`;

  // Set probabilities distribution bars
  const probs = res.probabilities || { Minor: 0, Serious: 0, Fatal: 0 };
  const fatalPct = ((probs.Fatal ?? 0) * 100).toFixed(1);
  const seriousPct = ((probs.Serious ?? 0) * 100).toFixed(1);
  const minorPct = ((probs.Minor ?? 0) * 100).toFixed(1);

  probFillFatal.style.width = `${fatalPct}%`;
  probValFatal.textContent = `${fatalPct}%`;
  probFillSerious.style.width = `${seriousPct}%`;
  probValSerious.textContent = `${seriousPct}%`;
  probFillMinor.style.width = `${minorPct}%`;
  probValMinor.textContent = `${minorPct}%`;

  // Set SHAP Contributing Weights
  shapBarContainer.innerHTML = "";
  const maxShap = Math.max(
    ...Object.values(res.shap_values || { x: 0 }).map(Math.abs),
  );

  res.top_contributing_features.forEach(fname => {
    const val = res.shap_values[fname] || 0;
    
    // Filter out factors with negligible impact (e.g., +0.000 or -0.000)
    if (Math.abs(val) < 0.0005) {
      return;
    }
    
    const isPositive = val >= 0;
    const absPercent =
      maxShap > 0 ? ((Math.abs(val) / maxShap) * 100).toFixed(1) : 0;

    const row = document.createElement("div");
    row.className = "shap-row";

    const label = document.createElement("span");
    label.className = "shap-label";
    label.textContent = getFriendlyFeatureName(fname);
    label.title = fname;

    const track = document.createElement("div");
    track.className = "shap-track";

    const bar = document.createElement("div");
    bar.className = `shap-bar ${isPositive ? "positive" : "negative"}`;
    bar.style.width = `${absPercent}%`;

    const valText = document.createElement("span");
    valText.className = "shap-val-text";
    valText.textContent = `${isPositive ? "+" : ""}${val.toFixed(3)}`;

    track.appendChild(bar);
    track.appendChild(valText);
    row.appendChild(label);
    row.appendChild(track);
    shapBarContainer.appendChild(row);
  });

  // Set report narrative
  shapExplanation.textContent =
    res.human_readable_explanation || "No explanation details generated.";

  // Set timestamp
  const now = new Date();
  predictionTimestamp.textContent = now.toLocaleString();

  // Smooth scroll to results
  setTimeout(() => {
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// 8. CLEAR RESET TRIGGER
clearBtn.addEventListener("click", () => {
  form.reset();

  // Update slider tooltip values manually
  if (speedLimitInput) {
    updateSpeedUI(speedLimitInput.value);
  }
  if (driverAgeInput) {
    updateAgeUI(driverAgeInput.value);
  }
  if (alcoholLabel) {
    alcoholLabel.textContent = "No";
  }

  // Remove all validation highlights and messages
  const requiredFields = form.querySelectorAll("[required]");
  requiredFields.forEach(clearFieldError);

  currentStep = 1;
  updateStepperUI();

  // Hide panels & reset values
  resultCard.classList.add("is-hidden");
  loaderCard.classList.add("is-hidden");
  resetResultsUI();
});

// 9. AUTO-OPEN DATE/TIME PICKERS ON CLICK
const dateInputEl = document.getElementById("accident-date");
const timeInputEl = document.getElementById("accident-time");

function handleDateTimeInteraction(e) {
  const el = e.target;
  const targetType = el.id === "accident-date" ? "date" : "time";

  if (el.type === "text") {
    el.type = targetType;
  }
  
  try {
    if (typeof el.showPicker === "function") {
      el.showPicker();
    }
  } catch (err) {
    // Ignore if picker is already open or unsupported
  }
}

function handleDateTimeBlur(e) {
  const el = e.target;
  if (!el.value) {
    el.type = "text";
  }
}

if (dateInputEl) {
  dateInputEl.addEventListener("click", handleDateTimeInteraction);
  dateInputEl.addEventListener("focus", handleDateTimeInteraction);
  dateInputEl.addEventListener("blur", handleDateTimeBlur);
}

if (timeInputEl) {
  timeInputEl.addEventListener("click", handleDateTimeInteraction);
  timeInputEl.addEventListener("focus", handleDateTimeInteraction);
  timeInputEl.addEventListener("blur", handleDateTimeBlur);
}
