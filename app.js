/* ========== Neural network (same logic, runs in browser) ========== */
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
let lastSpeakText = "";

function dot(a, b) { let s = 0; for (let i = 0; i < a.length; i++) s += a[i] * b[i]; return s; }
function matvec(mat, vec) { return mat.map((row) => dot(row, vec)); }
function add(a, b) { return a.map((v, i) => v + b[i]); }
function relu(x) { return x.map((v) => (v > 0 ? v : 0)); }
function softmax(logits) {
  const m = Math.max(...logits);
  const exps = logits.map((v) => Math.exp(v - m));
  const s = exps.reduce((acc, v) => acc + v, 0);
  return exps.map((e) => e / s);
}
function normalizeFeatures(features) {
  return features.map((value, i) => (value - BOUNDS[i][0]) / (BOUNDS[i][1] - BOUNDS[i][0]));
}
function predictProba(featuresNorm) {
  const z1 = add(matvec(model.W1, featuresNorm), model.b1);
  const a1 = relu(z1);
  const z2 = add(matvec(model.W2, a1), model.b2);
  return softmax(z2);
}

/* ========== Simple, farmer-friendly diagnosis ========== */
const SIMPLE_STATUS = {
  "Healthy": { icon: "✅", cls: "r-ok", title: "Plant is OK", short: "Your plant looks fine." },
  "Needs Water": { icon: "💧", cls: "r-water", title: "Needs Water", short: "Your plant needs water." },
  "Overwatered Risk": { icon: "⚠️", cls: "r-wet", title: "Too Much Water", short: "Soil has too much water." },
  "Heat/Light Stress": { icon: "☀️", cls: "r-stress", title: "Heat or Sun Problem", short: "Too hot, cold, or too much/too little sun." },
};

function simpleTips(label, readings) {
  const tips = [];
  const { soil_moisture: soil, temperature_c: temp, light_level: light, humidity: hum } = readings;
  if (label === "Needs Water") {
    tips.push({ ico: "💧", text: "Give water slowly to the soil." });
    tips.push({ ico: "⏳", text: "Check soil again after some hours." });
    if (hum < 35) tips.push({ ico: "💨", text: "Air is dry. Light mist can help." });
  } else if (label === "Overwatered Risk") {
    tips.push({ ico: "🛑", text: "Stop watering for now." });
    tips.push({ ico: "🕳️", text: "Make sure water can flow out of soil/pot." });
    if (light < 35) tips.push({ ico: "☀️", text: "More light can help soil dry." });
  } else if (label === "Heat/Light Stress") {
    if (temp > 29) tips.push({ ico: "🌳", text: "Move plant to a cooler or shaded place." });
    if (temp < 18) tips.push({ ico: "🧣", text: "Protect plant from cold wind." });
    if (light > 75) tips.push({ ico: "⛱️", text: "Too much sun. Give some shade." });
    if (light < 35) tips.push({ ico: "☀️", text: "Plant needs more light." });
    if (hum < 35) tips.push({ ico: "💨", text: "Air is dry. Add a little moisture around plant." });
    if (!tips.length) tips.push({ ico: "🌿", text: "Keep heat and sun balanced." });
  } else {
    tips.push({ ico: "👍", text: "Keep doing the same care." });
    tips.push({ ico: "👀", text: "Watch plant every day for changes." });
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

function diagnose() {
  if (!model) return;
  const readings = getReadings();
  const probs = predictProba(normalizeFeatures(FEATURE_NAMES.map((n) => readings[n])));
  const idx = probs.indexOf(Math.max(...probs));
  const label = LABELS[idx];
  const info = SIMPLE_STATUS[label];
  const tips = simpleTips(label, readings);

  lastSpeakText = info.short + " " + tips.map((t) => t.text).join(" ");

  document.getElementById("result-box").innerHTML = `
    <div class="result-main ${info.cls}">
      <div class="big-status">${info.icon}</div>
      <h3>${info.title}</h3>
      <p>${info.short}</p>
    </div>
    <ul class="advice-list">${tips.map((t) => `<li><span class="li-ico">${t.ico}</span><span>${t.text}</span></li>`).join("")}</ul>
    <div class="mini-readings">
      <div class="mini">💧 Water <strong>${readings.soil_moisture.toFixed(0)}</strong></div>
      <div class="mini">🌡️ Heat <strong>${readings.temperature_c.toFixed(1)}°C</strong></div>
      <div class="mini">☀️ Sun <strong>${readings.light_level.toFixed(0)}</strong></div>
      <div class="mini">💨 Air <strong>${readings.humidity.toFixed(0)}</strong></div>
    </div>`;
  document.getElementById("listen-btn").style.display = "inline-block";
}

function speakResult() {
  if (!lastSpeakText) return;
  if (!("speechSynthesis" in window)) { alert("Listen is not supported on this device/browser."); return; }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(lastSpeakText);
  u.rate = 0.9;
  window.speechSynthesis.speak(u);
}

async function loadModel() {
  const status = document.getElementById("model-status");
  try {
    const res = await fetch("./model_weights.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    model = await res.json();
    status.textContent = "Ready ✅";
    status.classList.remove("error");
  } catch (err) {
    status.textContent = `Problem loading plant brain (${err.message}).`;
    status.classList.add("error");
  }
}

/* ========== Weather (Open-Meteo, no API key) ========== */
function weatherCodeInfo(code) {
  const map = [
    [[0], "☀️", "Clear sky"],
    [[1, 2], "🌤️", "Partly cloudy"],
    [[3], "☁️", "Cloudy"],
    [[45, 48], "🌫️", "Fog"],
    [[51, 53, 55, 56, 57], "🌦️", "Light rain/drizzle"],
    [[61, 63, 65, 66, 67], "🌧️", "Rain"],
    [[71, 73, 75, 77], "🌨️", "Snow"],
    [[80, 81, 82], "🌧️", "Rain showers"],
    [[95, 96, 99], "⛈️", "Thunderstorm"],
  ];
  for (const [codes, icon, desc] of map) if (codes.includes(code)) return { icon, desc };
  return { icon: "🌤️", desc: "Weather" };
}

function weatherAdvice(cur) {
  const tips = [];
  const t = cur.temperature_2m, h = cur.relative_humidity_2m, r = cur.precipitation, w = cur.wind_speed_10m;
  if (r > 0.5) tips.push({ ico: "🌧️", text: "Rain expected/now. Do not add too much water." });
  else if (t > 32) tips.push({ ico: "💧", text: "Very hot. Plants may need more water (early morning/evening)." });
  else if (t < 15) tips.push({ ico: "🧣", text: "Cool weather. Protect young plants from cold." });
  else tips.push({ ico: "👍", text: "Weather is okay for normal farm work." });
  if (w > 35) tips.push({ ico: "💨", text: "Strong wind. Support weak plants." });
  if (h < 30) tips.push({ ico: "💨", text: "Air is dry. Plants may lose water faster." });
  if (h > 85) tips.push({ ico: "🍄", text: "Very humid. Watch for plant disease." });
  return tips;
}

async function checkWeather() {
  const status = document.getElementById("weather-status");
  const out = document.getElementById("weather-result");
  if (!navigator.geolocation) { status.textContent = "Location not supported on this device."; status.classList.add("error"); return; }
  status.textContent = "Getting your location…"; status.classList.remove("error"); out.innerHTML = "";
  navigator.geolocation.getCurrentPosition(async (pos) => {
    try {
      status.textContent = "Getting weather…";
      const { latitude: lat, longitude: lon } = pos.coords;
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=auto`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const cur = data.current;
      const info = weatherCodeInfo(cur.weather_code);
      const tips = weatherAdvice(cur);
      status.textContent = "Weather loaded ✅";
      out.innerHTML = `
        <div class="weather-card">
          <div class="weather-now">
            <div class="weather-icon">${info.icon}</div>
            <div>
              <div class="weather-temp">${cur.temperature_2m}°C</div>
              <div class="weather-desc">${info.desc}</div>
            </div>
          </div>
          <div class="weather-grid">
            <div class="wbox"><div class="wico">💧</div><div class="wval">${cur.relative_humidity_2m}%</div><div class="wlab">Air water</div></div>
            <div class="wbox"><div class="wico">🌧️</div><div class="wval">${cur.precipitation} mm</div><div class="wlab">Rain</div></div>
            <div class="wbox"><div class="wico">💨</div><div class="wval">${cur.wind_speed_10m} km/h</div><div class="wlab">Wind</div></div>
          </div>
          <div class="advice-box">
            <h3>🌱 Farm advice</h3>
            <ul class="advice-list">${tips.map((t) => `<li><span class="li-ico">${t.ico}</span><span>${t.text}</span></li>`).join("")}</ul>
          </div>
        </div>`;
    } catch (err) {
      status.textContent = `Could not get weather (${err.message}).`; status.classList.add("error");
    }
  }, (err) => {
    status.textContent = "Location not allowed. Please allow location to check weather."; status.classList.add("error");
  });
}

/* ========== Plant Encyclopedia ========== */
const PLANTS = [
  { emoji: "🌽", name: "Maize (Corn)", lifespan: "3–5 months (one season)", water: "Medium", sun: "Full sun", weaknesses: ["Fall armyworm", "Stem borer", "Maize streak virus", "Drought at flowering"], care: "Plant in well-drained soil. Weed early. Add fertilizer when young." },
  { emoji: "🌾", name: "Rice", lifespan: "3–6 months", water: "High (needs much water)", sun: "Full sun", weaknesses: ["Rice blast disease", "Stem borer", "Brown planthopper", "Flooding or drought"], care: "Keep water level steady in paddy. Use healthy seedlings." },
  { emoji: "🌿", name: "Cassava", lifespan: "9–18 months to harvest", water: "Low to medium", sun: "Full sun", weaknesses: ["Cassava mosaic disease", "Mealybugs", "Root rot in wet soil", "Poor soil"], care: "Plant stem cuttings in loose soil. Avoid waterlogged land." },
  { emoji: "🍅", name: "Tomato", lifespan: "3–6 months", water: "Medium (regular)", sun: "Full sun", weaknesses: ["Blight", "Wilt", "Aphids/whiteflies", "Fruit cracking"], care: "Stake plants. Water soil, not leaves. Remove diseased leaves." },
  { emoji: "🍠", name: "Yam", lifespan: "6–10 months", water: "Medium", sun: "Full sun", weaknesses: ["Yam beetle", "Nematodes", "Tuber rot", "Anthracnose"], care: "Plant in mounds/ridges with good drainage. Use healthy seed yams." },
  { emoji: "🫘", name: "Beans", lifespan: "2–4 months", water: "Medium", sun: "Full sun", weaknesses: ["Aphids", "Bean rust", "Root rot", "Too much rain"], care: "Do not overwater. Rotate crops to keep soil healthy." },
  { emoji: "🌶️", name: "Pepper", lifespan: "4–6 months (can fruit longer)", water: "Medium", sun: "Full sun", weaknesses: ["Leaf curl virus", "Aphids/thrips", "Fruit rot", "Drought stress"], care: "Water regularly but avoid soggy soil. Harvest ripe fruits often." },
  { emoji: "🍌", name: "Plantain/Banana", lifespan: "9–12 months to fruit (plant lives several years by suckers)", water: "High", sun: "Full sun to partial shade", weaknesses: ["Black sigatoka", "Nematodes", "Banana weevil", "Strong wind damage"], care: "Needs rich soil and regular water. Remove old leaves and excess suckers." },
  { emoji: "🥬", name: "Okra", lifespan: "2–4 months", water: "Medium", sun: "Full sun", weaknesses: ["Flea beetles", "Aphids", "Powdery mildew", "Poor flowering in cold"], care: "Harvest pods young. Keep soil moist but not waterlogged." },
  { emoji: "🥜", name: "Groundnut (Peanut)", lifespan: "3–5 months", water: "Low to medium", sun: "Full sun", weaknesses: ["Leaf spot", "Rosette virus", "Aphids", "Drought at pegging"], care: "Grow in loose, sandy soil. Avoid too much nitrogen fertilizer." },
  { emoji: "🥔", name: "Potato", lifespan: "3–4 months", water: "Medium (regular)", sun: "Full sun", weaknesses: ["Late blight", "Potato beetle", "Tuber rot", "Waterlogging"], care: "Hill soil around stems. Keep moisture even, avoid wet leaves." },
  { emoji: "🥭", name: "Mango (tree)", lifespan: "Many years (can bear 30+ years)", water: "Low to medium once grown", sun: "Full sun", weaknesses: ["Anthracnose", "Fruit flies", "Powdery mildew", "Frost/cold damage"], care: "Prune lightly. Protect flowers/fruit from disease and pests." },
];

function renderPlants(filter = "") {
  const q = filter.trim().toLowerCase();
  const list = PLANTS.filter((p) => p.name.toLowerCase().includes(q) || p.weaknesses.join(" ").toLowerCase().includes(q));
  const el = document.getElementById("plant-list");
  if (!list.length) { el.innerHTML = `<p class="status">No plant found.</p>`; return; }
  el.innerHTML = list.map((p) => `
    <article class="plant-card">
      <div class="plant-head"><div class="plant-emoji">${p.emoji}</div><h3>${p.name}</h3></div>
      <div class="plant-meta">
        <div class="meta-row"><strong>⏳ Life/span:</strong> ${p.lifespan}</div>
        <div class="meta-row"><strong>💧 Water need:</strong> ${p.water}</div>
        <div class="meta-row"><strong>☀️ Sun need:</strong> ${p.sun}</div>
        <div class="meta-row"><strong>⚠️ Weakness/problems:</strong><br>${p.weaknesses.map((w) => `<span class="pill">${w}</span>`).join("")}</div>
        <div class="meta-row"><strong>🌱 Care:</strong> ${p.care}</div>
      </div>
    </article>`).join("");
}

/* ========== Navigation & init ========== */
function showSection(id) {
  document.querySelectorAll(".section").forEach((s) => s.classList.toggle("active", s.id === id));
  document.querySelectorAll(".nav-link").forEach((a) => a.classList.toggle("active", a.dataset.section === id));
  document.getElementById("sidebar").classList.remove("open");
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setup() {
  // Nav
  document.querySelectorAll(".nav-link").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); showSection(a.dataset.section); }));
  document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => showSection(b.dataset.go)));
  document.getElementById("menu-btn").addEventListener("click", () => document.getElementById("sidebar").classList.toggle("open"));

  // Sliders
  for (const name of FEATURE_NAMES) {
    const input = document.getElementById(name);
    const out = document.getElementById(`${name}_val`);
    input.addEventListener("input", () => { out.textContent = input.value; });
  }

  // Diagnose
  document.getElementById("diagnose-btn").addEventListener("click", diagnose);
  document.getElementById("listen-btn").addEventListener("click", speakResult);

  // Weather
  document.getElementById("weather-btn").addEventListener("click", checkWeather);

  // Encyclopedia
  renderPlants();
  document.getElementById("plant-search").addEventListener("input", (e) => renderPlants(e.target.value));

  // Initial section from hash
  const hash = (location.hash || "#home").replace("#", "");
  if (document.getElementById(hash)) showSection(hash);
}

setup();
loadModel();
