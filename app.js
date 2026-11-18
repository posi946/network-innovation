const FEATURE_NAMES = ["soil_moisture", "temperature_c", "light_level", "humidity"];
const LABELS = ["Healthy", "Needs Water", "Overwatered Risk", "Heat/Light Stress"];
const HEALTHY_RANGES = {
  soil_moisture: [35, 65],
  temperature_c: [18, 29],
  light_level: [35, 75],
  humidity: [35, 70],
};
const BOUNDS = [[0, 100], [5, 45], [0, 100], [10, 100]];

let model = null;

function dot(a, b) {
  let s = 0;
  for (let i = 0; i < a.length; i++) s += a[i] * b[i];
  return s;
}

function matvec(mat, vec) {
  return mat.map((row) => dot(row, vec));
}

function add(a, b) {
  return a.map((v, i) => v + b[i]);
}

function relu(x) {
  return x.map((v) => (v > 0 ? v : 0));
}

function softmax(logits) {
  const m = Math.max(...logits);
  const exps = logits.map((v) => Math.exp(v - m));
  const s = exps.reduce((acc, v) => acc + v, 0);
  return exps.map((e) => e / s);
}

function normalizeFeatures(features) {
  return features.map((value, i) => {
    const [lo, hi] = BOUNDS[i];
    return (value - lo) / (hi - lo);
  });
}

function predictProba(featuresNorm) {
  const z1 = add(matvec(model.W1, featuresNorm), model.b1);
  const a1 = relu(z1);
  const z2 = add(matvec(model.W2, a1), model.b2);
  return softmax(z2);
}

function statusForValue(name, value) {
  const [lo, hi] = HEALTHY_RANGES[name];
  if (value < lo) return "low";
  if (value > hi) return "high";
  return "ok";
}

function analyzeReadings(readings) {
  const notes = [];
  for (const name of FEATURE_NAMES) {
    const value = readings[name];
    const [lo, hi] = HEALTHY_RANGES[name];
    const status = statusForValue(name, value);
    const label = name.replace(/_/g, " ");
    if (status === "low") notes.push(`${label} is low (${value.toFixed(1)}; healthy ~${lo}-${hi}).`);
    else if (status === "high") notes.push(`${label} is high (${value.toFixed(1)}; healthy ~${lo}-${hi}).`);
  }
  if (!notes.length) notes.push("All monitored readings are within the healthy range.");
  return notes;
}

function recommend(label, readings, confidence) {
  const tips = [];
  const soil = readings.soil_moisture;
  const temp = readings.temperature_c;
  const light = readings.light_level;
  const hum = readings.humidity;

  if (label === "Needs Water") {
    tips.push("Water the plant gradually and check that excess water can drain.");
    if (hum < HEALTHY_RANGES.humidity[0]) {
      tips.push("Increase humidity slightly (mist nearby air or use a pebble tray) to reduce drying stress.");
    }
    tips.push("Recheck soil moisture in a few hours before watering again.");
  } else if (label === "Overwatered Risk") {
    tips.push("Pause watering and let the top soil dry before the next watering.");
    tips.push("Ensure the pot has drainage and the roots are not sitting in water.");
    if (light < HEALTHY_RANGES.light_level[0]) {
      tips.push("Provide a bit more light to help the soil dry at a healthy rate.");
    }
  } else if (label === "Heat/Light Stress") {
    if (temp > HEALTHY_RANGES.temperature_c[1]) tips.push("Move the plant to a cooler spot and avoid hot afternoon sun.");
    if (temp < HEALTHY_RANGES.temperature_c[0]) tips.push("Move the plant away from cold drafts and keep temperature more stable.");
    if (light > HEALTHY_RANGES.light_level[1]) tips.push("Reduce direct light exposure or diffuse harsh light.");
    if (light < HEALTHY_RANGES.light_level[0]) tips.push("Increase light exposure gradually (brighter window or grow light).");
    if (hum < HEALTHY_RANGES.humidity[0]) tips.push("Raise humidity moderately if leaves look dry or curled.");
    if (!tips.length) tips.push("Stabilize temperature, light, and humidity to reduce environmental stress.");
  } else {
    tips.push("Keep the current care routine stable and monitor changes over time.");
    tips.push("Make small adjustments only if one reading trends out of range.");
  }

  if (confidence < 0.55) {
    tips.unshift("Confidence is moderate—take a second reading soon to confirm before major changes.");
  }
  return tips;
}

function getReadings() {
  return {
    soil_moisture: parseFloat(document.getElementById("soil_moisture").value),
    temperature_c: parseFloat(document.getElementById("temperature_c").value),
    light_level: parseFloat(document.getElementById("light_level").value),
    humidity: parseFloat(document.getElementById("humidity").value),
  };
}

function badgeClass(label) {
  return label.replace(/\//g, "-").replace(/\s+/g, "-");
}

function renderResult(readings, probs) {
  const labelIndex = probs.indexOf(Math.max(...probs));
  const label = LABELS[labelIndex];
  const confidence = probs[labelIndex];
  const notes = analyzeReadings(readings);
  const tips = recommend(label, readings, confidence);

  const probsHtml = LABELS.map((name, i) => {
    const pct = (probs[i] * 100).toFixed(1);
    return `<div class="prob-row"><span>${name}</span><div class="bar"><span style="width:${pct}%"></span></div><span>${pct}%</span></div>`;
  }).join("");

  document.getElementById("result-content").innerHTML = `
    <div class="result">
      <div>
        <span class="badge ${badgeClass(label)}">${label}</span>
        <span class="muted"> &nbsp;${(confidence * 100).toFixed(1)}% confidence</span>
      </div>
      <div>
        <div class="section-title">Sensor readings</div>
        <ul>
          ${FEATURE_NAMES.map((n) => `<li>${n.replace(/_/g, " ")}: <strong>${readings[n].toFixed(1)}</strong></li>`).join("")}
        </ul>
      </div>
      <div>
        <div class="section-title">Assistant observations</div>
        <ul>${notes.map((n) => `<li>${n}</li>`).join("")}</ul>
      </div>
      <div>
        <div class="section-title">Recommended actions</div>
        <ul>${tips.map((t) => `<li>${t}</li>`).join("")}</ul>
      </div>
      <div>
        <div class="section-title">Model probabilities</div>
        <div class="probs">${probsHtml}</div>
      </div>
    </div>`;
}

function diagnose() {
  if (!model) return;
  const readings = getReadings();
  const features = FEATURE_NAMES.map((n) => readings[n]);
  const probs = predictProba(normalizeFeatures(features));
  renderResult(readings, probs);
}

const SAMPLES = [
  { title: "Balanced plant", values: { soil_moisture: 55, temperature_c: 24, light_level: 60, humidity: 50 } },
  { title: "Dry soil", values: { soil_moisture: 18, temperature_c: 27, light_level: 65, humidity: 35 } },
  { title: "Soggy soil", values: { soil_moisture: 85, temperature_c: 22, light_level: 45, humidity: 60 } },
  { title: "Hot and bright", values: { soil_moisture: 50, temperature_c: 36, light_level: 92, humidity: 25 } },
];

function applySample(sample) {
  for (const [k, v] of Object.entries(sample.values)) {
    const input = document.getElementById(k);
    input.value = v;
    document.getElementById(`${k}_val`).textContent = String(v);
  }
  diagnose();
}

function setup() {
  for (const name of FEATURE_NAMES) {
    const input = document.getElementById(name);
    const out = document.getElementById(`${name}_val`);
    input.addEventListener("input", () => { out.textContent = input.value; });
  }
  document.getElementById("diagnose-form").addEventListener("submit", (e) => {
    e.preventDefault();
    diagnose();
  });
  document.getElementById("demo-btn").addEventListener("click", () => {
    let i = parseInt(document.body.dataset.sampleIndex || "0", 10);
    const sample = SAMPLES[i % SAMPLES.length];
    document.body.dataset.sampleIndex = String(i + 1);
    applySample(sample);
    const status = document.getElementById("model-status");
    status.textContent = `Showing sample: ${sample.title}. Click again for next scenario.`;
    status.classList.remove("error");
  });
}

async function loadModel() {
  const status = document.getElementById("model-status");
  try {
    const res = await fetch("./model_weights.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    model = await res.json();
    status.textContent = "Neural network loaded. Ready to diagnose.";
    status.classList.remove("error");
  } catch (err) {
    status.textContent = `Could not load model weights (${err.message}). Ensure model_weights.json is deployed with the site.`;
    status.classList.add("error");
  }
}

setup();
loadModel();
