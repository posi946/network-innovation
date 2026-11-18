/* ========== Neural network (browser inference) ========== */
const FEATURE_NAMES = ["soil_moisture", "temperature_c", "light_level", "humidity"];
const LABELS = ["Healthy", "Needs Water", "Overwatered Risk", "Heat/Light Stress"];
const BOUNDS = [[0, 100], [5, 45], [0, 100], [10, 100]];
let model = null;
let lastSpeakText = "";
let lastDiagnosis = null;
let lastWeather = null;

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

async function loadModel() {
  const status = document.getElementById("model-status");
  try {
    const res = await fetch("./model_weights.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    model = await res.json();
    status.textContent = "Model loaded and ready.";
    status.classList.remove("error");
  } catch (err) {
    status.textContent = `Unable to load model weights (${err.message}). Ensure model_weights.json is available.`;
    status.classList.add("error");
  }
}

/* ========== Diagnosis ========== */
const STATUS_META = {
  "Healthy": { cls: "r-ok", title: "Healthy", summary: "Conditions are within a generally favorable range." },
  "Needs Water": { cls: "r-water", title: "Needs Water", summary: "Moisture levels indicate likely water deficit." },
  "Overwatered Risk": { cls: "r-wet", title: "Overwatered Risk", summary: "Moisture levels indicate potential excess water or poor drainage risk." },
  "Heat/Light Stress": { cls: "r-stress", title: "Heat/Light Stress", summary: "Temperature, light, or humidity conditions indicate environmental stress." },
};

function getReadings() {
  return {
    soil_moisture: parseFloat(document.getElementById("soil_moisture").value),
    temperature_c: parseFloat(document.getElementById("temperature_c").value),
    light_level: parseFloat(document.getElementById("light_level").value),
    humidity: parseFloat(document.getElementById("humidity").value),
  };
}

function recommendations(label, r) {
  const tips = [];
  if (label === "Needs Water") {
    tips.push("Irrigate gradually and allow water to penetrate the root zone without runoff.");
    tips.push("Recheck soil moisture after irrigation before repeating.");
    if (r.humidity < 35) tips.push("Low ambient humidity may increase evapotranspiration; monitor moisture more frequently.");
    if (r.temperature_c > 30) tips.push("High temperatures can accelerate drying; consider early-morning or evening watering.");
  } else if (label === "Overwatered Risk") {
    tips.push("Pause irrigation and allow the substrate/soil to drain and partially dry.");
    tips.push("Verify drainage pathways and avoid standing water around roots.");
    if (r.light_level < 35) tips.push("Low light can slow drying; improve light exposure where appropriate.");
  } else if (label === "Heat/Light Stress") {
    if (r.temperature_c > 29) tips.push("Reduce heat exposure (shade, ventilation, or timing adjustments) during peak temperatures.");
    if (r.temperature_c < 18) tips.push("Protect plants from cold stress, drafts, or low nighttime temperatures.");
    if (r.light_level > 75) tips.push("Excessive light intensity may require shading or diffusion.");
    if (r.light_level < 35) tips.push("Insufficient light may limit growth; increase exposure gradually where feasible.");
    if (r.humidity < 35) tips.push("Low humidity can exacerbate stress; consider humidity management where practical.");
    if (!tips.length) tips.push("Stabilize temperature, light, and humidity to reduce environmental stress.");
  } else {
    tips.push("Maintain current management practices and continue routine monitoring.");
    tips.push("Adjust inputs incrementally if any parameter trends outside the optimal range.");
  }
  return tips;
}

function diagnose() {
  if (!model) return;
  const r = getReadings();
  const probs = predictProba(normalizeFeatures(FEATURE_NAMES.map((n) => r[n])));
  const idx = probs.indexOf(Math.max(...probs));
  const label = LABELS[idx];
  const confidence = probs[idx];
  const meta = STATUS_META[label];
  const tips = recommendations(label, r);

  lastSpeakText = `${meta.title}. ${meta.summary} Recommendations: ${tips.join(" ")}`;
  lastDiagnosis = { label, confidence, summary: meta.summary, readings: r, tips, time: new Date() };

  document.getElementById("result-box").innerHTML = `
    <div class="result-head ${meta.cls}">
      <h3>${meta.title}</h3>
      <p>${meta.summary}</p>
      <p class="subtle">Model confidence: ${(confidence * 100).toFixed(1)}%</p>
    </div>
    <div class="metrics">
      <div class="metric"><div class="label">Soil moisture</div><div class="value">${r.soil_moisture.toFixed(0)}%</div></div>
      <div class="metric"><div class="label">Temperature</div><div class="value">${r.temperature_c.toFixed(1)}°C</div></div>
      <div class="metric"><div class="label">Light exposure</div><div class="value">${r.light_level.toFixed(0)}%</div></div>
      <div class="metric"><div class="label">Humidity</div><div class="value">${r.humidity.toFixed(0)}%</div></div>
    </div>
    <h3>Recommendations</h3>
    <ul class="rec-list">${tips.map((t) => `<li>${t}</li>`).join("")}</ul>
    <p class="subtle">Inference runs locally in your browser using a trained feedforward neural network (4→12→4). Use as decision support alongside field observation.</p>
  `;
  const listenBtn = document.getElementById("listen-btn");
  listenBtn.style.display = "inline-flex";
}

function speakResult() {
  if (!lastSpeakText) return;
  if (!("speechSynthesis" in window)) { alert("Speech synthesis is not supported in this browser."); return; }
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(lastSpeakText);
  u.rate = 0.95;
  window.speechSynthesis.speak(u);
}

/* ========== Weather (Open-Meteo) ========== */
function weatherCodeInfo(code) {
  const map = [
    [[0], "Clear sky"],
    [[1], "Mainly clear"], [[2], "Partly cloudy"], [[3], "Overcast"],
    [[45, 48], "Fog / rime fog"],
    [[51, 53, 55], "Drizzle"], [[56, 57], "Freezing drizzle"],
    [[61, 63, 65], "Rain"], [[66, 67], "Freezing rain"],
    [[71, 73, 75], "Snowfall"], [[77], "Snow grains"],
    [[80, 81, 82], "Rain showers"], [[85, 86], "Snow showers"],
    [[95], "Thunderstorm"], [[96, 99], "Thunderstorm with hail"],
  ];
  for (const [codes, desc] of map) if (codes.includes(code)) return desc;
  return "Variable conditions";
}

function weatherAdvice(cur) {
  const tips = [];
  const t = cur.temperature_2m, h = cur.relative_humidity_2m, r = cur.precipitation, w = cur.wind_speed_10m;
  if (r >= 1) tips.push("Precipitation detected: defer or reduce irrigation and assess drainage to prevent waterlogging.");
  else if (r > 0) tips.push("Light precipitation: account for added moisture before irrigating.");
  if (t >= 33) tips.push("High temperature: increase monitoring for moisture stress; irrigate during cooler periods where possible.");
  if (t <= 12) tips.push("Low temperature: protect sensitive crops and delay temperature-sensitive operations as appropriate.");
  if (w >= 35) tips.push("Elevated wind speeds: secure structures/supports and consider wind protection for vulnerable plants.");
  if (h <= 30) tips.push("Low humidity: higher evapotranspiration likely; adjust irrigation and mulching strategies.");
  if (h >= 85) tips.push("High humidity: increased disease pressure possible; prioritize airflow and monitoring for fungal/bacterial issues.");
  if (!tips.length) tips.push("Conditions appear moderate; proceed with standard field operations and routine monitoring.");
  return tips;
}

async function checkWeather() {
  const status = document.getElementById("weather-status");
  const out = document.getElementById("weather-result");
  if (!navigator.geolocation) { status.textContent = "Geolocation is not supported by this browser."; status.classList.add("error"); return; }
  status.textContent = "Requesting location…"; status.classList.remove("error"); out.innerHTML = "";

  navigator.geolocation.getCurrentPosition(async (pos) => {
    try {
      status.textContent = "Fetching current conditions…";
      const { latitude: lat, longitude: lon } = pos.coords;
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m&timezone=auto`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const cur = data.current;
      const desc = weatherCodeInfo(cur.weather_code);
      const tips = weatherAdvice(cur);
      lastWeather = { lat, lon, timezone: data.timezone || "local", current: cur, desc, tips, time: new Date() };
      status.textContent = `Location: ${lat.toFixed(3)}, ${lon.toFixed(3)} • Timezone: ${data.timezone || "local"}`;
      out.innerHTML = `
        <div class="weather-wrap">
          <div class="weather-summary">
            <div>
              <div class="weather-big">${cur.temperature_2m}°C</div>
              <div class="weather-desc">${desc}</div>
            </div>
          </div>
          <div class="weather-metrics">
            <div class="metric"><div class="label">Humidity</div><div class="value">${cur.relative_humidity_2m}%</div></div>
            <div class="metric"><div class="label">Precipitation</div><div class="value">${cur.precipitation} mm</div></div>
            <div class="metric"><div class="label">Wind speed</div><div class="value">${cur.wind_speed_10m} km/h</div></div>
          </div>
          <div class="advice-panel">
            <h3>Operational guidance</h3>
            <ul class="rec-list">${tips.map((t) => `<li>${t}</li>`).join("")}</ul>
          </div>
        </div>`;
    } catch (err) {
      status.textContent = `Unable to retrieve weather (${err.message}).`;
      status.classList.add("error");
    }
  }, () => {
    status.textContent = "Location access denied or unavailable. Enable location permissions to use this feature.";
    status.classList.add("error");
  });
}

/* ========== Knowledge Network (encyclopedia) ========== */
let activeCategory = "All";
let searchQuery = "";

function getCategories() {
  const set = new Set((KNOWLEDGE_BASE || []).map((e) => e.category));
  return ["All", ...Array.from(set)];
}

function entryText(e) {
  return [e.name, e.scientificName, e.category, e.lifespan, e.conditions, (e.vulnerabilities||[]).join(" "), e.management, e.impact, e.notes].join(" ").toLowerCase();
}

function renderFilters() {
  const cats = getCategories();
  const wrap = document.getElementById("category-filters");
  wrap.innerHTML = cats.map((c) => `<button class="filter-btn ${c===activeCategory?"active":""}" data-cat="${c}">${c}</button>`).join("");
  wrap.querySelectorAll(".filter-btn").forEach((btn) => btn.addEventListener("click", () => {
    activeCategory = btn.dataset.cat;
    renderFilters();
    renderKnowledge();
  }));
}

function typeClass(cat) { return (cat || "").replace(/[^a-zA-Z]/g, "-"); }

function renderKnowledge() {
  const q = searchQuery.trim().toLowerCase();
  let list = (KNOWLEDGE_BASE || []).filter((e) => activeCategory === "All" || e.category === activeCategory);
  if (q) list = list.filter((e) => entryText(e).includes(q));

  document.getElementById("result-count").textContent = `${list.length} entr${list.length === 1 ? "y" : "ies"} shown (${(KNOWLEDGE_BASE||[]).length} total in network)`;

  const el = document.getElementById("plant-list");
  if (!list.length) { el.innerHTML = `<div class="card"><p class="status">No entries match the current filters.</p></div>`; return; }

  el.innerHTML = list.map((e) => `
    <article class="k-card">
      <div class="k-head">
        <div>
          <h3 class="k-title">${e.name}</h3>
          <p class="k-sci">${e.scientificName || ""}</p>
        </div>
        <span class="k-type ${typeClass(e.category)}">${e.category}</span>
      </div>
      <div class="k-body">
        <div class="k-row"><strong>Lifespan / cycle:</strong> ${e.lifespan || "—"}</div>
        <div class="k-row"><strong>Conditions:</strong> ${e.conditions || "—"}</div>
        <div class="k-row"><strong>Vulnerabilities / weaknesses:</strong>
          <div class="tags">${(e.vulnerabilities||[]).map((v)=>`<span class="tag">${v}</span>`).join("") || "—"}</div>
        </div>
        <details class="k-more">
          <summary>Management, impact, and notes</summary>
          <div class="k-body" style="margin-top:8px">
            <div class="k-row"><strong>Management / control:</strong> ${e.management || "—"}</div>
            <div class="k-row"><strong>Impact / use:</strong> ${e.impact || "—"}</div>
            <div class="k-row"><strong>Notes:</strong> ${e.notes || "—"}</div>
          </div>
        </details>
      </div>
    </article>`).join("");
}

/* ========== Assistant (local conversational layer) ========== */
function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function addChatMessage(role, html) {
  const box = document.getElementById("chat-messages");
  if (!box) return;
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  div.innerHTML = html;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

function scoreEntry(e, q) {
  const ql = q.toLowerCase();
  const tokens = ql.split(/[^a-z0-9]+/).filter(t => t.length > 2);
  let score = 0;
  const name = (e.name || "").toLowerCase();
  const sci = (e.scientificName || "").toLowerCase();
  if (name.includes(ql) || ql.includes(name.split(/[\s(]/)[0].toLowerCase())) score += 12;
  if (sci.includes(ql)) score += 10;
  for (const t of tokens) {
    if (name.includes(t)) score += 5;
    if (sci.includes(t)) score += 4;
    if ((e.category || "").toLowerCase().includes(t)) score += 2;
    if ((e.conditions || "").toLowerCase().includes(t)) score += 1;
    if ((e.vulnerabilities || []).join(" ").toLowerCase().includes(t)) score += 2;
    if ((e.management || "").toLowerCase().includes(t)) score += 2;
    if ((e.impact || "").toLowerCase().includes(t)) score += 1;
    if ((e.notes || "").toLowerCase().includes(t)) score += 1;
  }
  return score;
}

function searchKnowledge(query, limit = 3) {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return (KNOWLEDGE_BASE || [])
    .map(e => ({ e, score: scoreEntry(e, q) }))
    .filter(x => x.score > 0)
    .sort((a,b) => b.score - a.score)
    .slice(0, limit)
    .map(x => x.e);
}

function formatEntryBrief(e) {
  const vul = (e.vulnerabilities || []).slice(0, 5).map(v => `<li>${escapeHtml(v)}</li>`).join("");
  return `<div>
    <p><strong>${escapeHtml(e.name)}</strong> ${e.scientificName ? `<em>(${escapeHtml(e.scientificName)})</em>` : ""} — ${escapeHtml(e.category || "")}</p>
    <p><strong>Lifespan/cycle:</strong> ${escapeHtml(e.lifespan || "—")}<br>
    <strong>Conditions:</strong> ${escapeHtml(e.conditions || "—")}</p>
    <p><strong>Key vulnerabilities/weaknesses:</strong></p><ul>${vul || "<li>—</li>"}</ul>
    <p><strong>Management/control:</strong> ${escapeHtml(e.management || "—")}</p>
    <p><strong>Impact/use:</strong> ${escapeHtml(e.impact || "—")}</p>
  </div>`;
}

function generateAssistantReply(raw) {
  const text = raw.trim();
  const q = text.toLowerCase();
  if (!text) return "Please enter a question.";

  // Greetings / help
  if (/\b(hello|hi|hey|greetings)\b/.test(q)) {
    return "Hello. I can help with: interpreting your latest plant diagnosis, weather-informed decisions, and detailed information on crops, weeds, and special plants in the knowledge network. What would you like to know?";
  }
  if (/\b(help|what can you do|how to use)\b/.test(q)) {
    return "I can: (1) explain your latest diagnosis and recommendations, (2) summarize weather guidance if you’ve checked Weather Insights, and (3) answer questions using the encyclopedia (e.g. lifespan, vulnerabilities/weaknesses, management/control, and impact for 60+ plants and weeds). Try asking about a specific plant/weed or ‘explain my latest diagnosis’.";
  }
  if (/\b(thank|thanks)\b/.test(q)) {
    return "You’re welcome. If you need details on a specific crop, weed, or your diagnosis, ask anytime.";
  }

  // Diagnosis intent
  if (/\b(diagnos|my plant|my result|latest result|status|what should i do|recommendation|assessment)\b/.test(q) && !/\b(weed|encyclopedia)\b/.test(q)) {
    if (!lastDiagnosis) {
      return "No diagnosis is available yet. Go to <strong>Plant Diagnosis</strong>, set the conditions, and run the assessment — then I can explain the result and recommendations.";
    }
    const d = lastDiagnosis;
    const tips = d.tips.map(t => `<li>${escapeHtml(t)}</li>`).join("");
    return `<p><strong>Latest diagnosis:</strong> ${escapeHtml(d.label)} (${(d.confidence*100).toFixed(1)}% confidence)</p>
      <p>${escapeHtml(d.summary)}</p>
      <p><strong>Inputs:</strong> soil moisture ${d.readings.soil_moisture.toFixed(0)}%, temperature ${d.readings.temperature_c.toFixed(1)}°C, light ${d.readings.light_level.toFixed(0)}%, humidity ${d.readings.humidity.toFixed(0)}%.</p>
      <p><strong>Recommendations:</strong></p><ul>${tips}</ul>`;
  }

  // Weather intent
  if (/\b(weather|rain|forecast|temperature outside|humidity outside|wind)\b/.test(q)) {
    if (lastWeather) {
      const w = lastWeather;
      const tips = w.tips.map(t => `<li>${escapeHtml(t)}</li>`).join("");
      return `<p><strong>Latest weather context:</strong> ${w.current.temperature_2m}°C, ${escapeHtml(w.desc)}, humidity ${w.current.relative_humidity_2m}%, precipitation ${w.current.precipitation} mm, wind ${w.current.wind_speed_10m} km/h (location ${w.lat.toFixed(3)}, ${w.lon.toFixed(3)}).</p>
        <p><strong>Operational guidance:</strong></p><ul>${tips}</ul>
        <p class="subtle">For updated conditions, use <strong>Weather Insights</strong> again.</p>`;
    }
    return "I don’t have current weather data yet. Open <strong>Weather Insights</strong> and use your location to fetch conditions; I can then help interpret them for irrigation and field decisions.";
  }

  // Knowledge network search
  const matches = searchKnowledge(text, 3);
  if (matches.length) {
    if (matches.length === 1) {
      return `<p>From the knowledge network:</p>${formatEntryBrief(matches[0])}<p>Open <strong>Encyclopedia</strong> to view full details and related entries.</p>`;
    }
    const blocks = matches.map((e, i) => `<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">${formatEntryBrief(e)}`).join("");
    return `<p>Top matches from the knowledge network:</p>${blocks}<p>Open <strong>Encyclopedia</strong> for more entries and filters.</p>`;
  }

  // Generic domain hints
  if (/\b(weed|weeds)\b/.test(q)) {
    return "I can provide management and control guidance for weeds in the encyclopedia (e.g. Striga, speargrass, nutgrass, parthenium, water hyacinth). Ask about a specific weed by name.";
  }
  if (/\b(drought|dry|resistant|tolerant)\b/.test(q)) {
    return "Several entries note drought tolerance or water sensitivity (e.g. sorghum, millet, cassava, moringa, date palm). Ask for a specific crop, or search in <strong>Encyclopedia</strong> for ‘drought’ to compare conditions and vulnerabilities.";
  }

  return "I couldn’t find a direct match in the knowledge network. Try asking with a plant/weed name (e.g. ‘tomato vulnerabilities’, ‘how to control speargrass’) or ask me to explain your latest diagnosis. You can also browse <strong>Encyclopedia</strong> with filters and search.";
}

function handleChatSubmit(text) {
  const t = text.trim();
  if (!t) return;
  addChatMessage("user", `<p>${escapeHtml(t)}</p>`);
  const reply = generateAssistantReply(t);
  addChatMessage("assistant", reply);
}

function initAssistant() {
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  if (!form || !input) return;
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const t = input.value;
    input.value = "";
    handleChatSubmit(t);
  });
  document.querySelectorAll("#chat-suggestions .chip").forEach((btn) => {
    btn.addEventListener("click", () => handleChatSubmit(btn.dataset.prompt || btn.textContent));
  });
  addChatMessage("assistant", `<p><strong>PlantGuard Assistant</strong> is ready.</p><p>I can explain your latest neural diagnosis, provide weather-informed guidance, and answer questions from the knowledge network (60+ plants, weeds, and special species). Ask me anything to get started.</p>`);
}

/* ========== Navigation & init ========== */
function showSection(id) {
  document.querySelectorAll(".section").forEach((s) => s.classList.toggle("active", s.id === id));
  document.querySelectorAll(".nav-link").forEach((a) => a.classList.toggle("active", a.dataset.section === id));
  document.getElementById("sidebar").classList.remove("open");
  if (location.hash !== "#" + id) history.replaceState(null, "", "#" + id);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function getPreferredTheme() {
  const saved = localStorage.getItem("pg-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  const t = theme === "dark" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", t);
  const btn = document.getElementById("theme-btn");
  if (btn) {
    const next = t === "dark" ? "light" : "dark";
    btn.textContent = next === "dark" ? "Dark mode" : "Light mode";
    btn.setAttribute("aria-label", `Switch to ${next} mode`);
    btn.title = `Switch to ${next} mode`;
  }
}

function initTheme() {
  applyTheme(getPreferredTheme());
  const btn = document.getElementById("theme-btn");
  if (btn) {
    btn.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
      const next = current === "dark" ? "light" : "dark";
      localStorage.setItem("pg-theme", next);
      applyTheme(next);
    });
  }
  if (window.matchMedia) {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e) => {
      if (!localStorage.getItem("pg-theme")) applyTheme(e.matches ? "dark" : "light");
    };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange);
  }
}

function setup() {
  initTheme();
  document.querySelectorAll(".nav-link").forEach((a) => a.addEventListener("click", (e) => { e.preventDefault(); showSection(a.dataset.section); }));
  document.querySelectorAll("[data-go]").forEach((b) => b.addEventListener("click", () => showSection(b.dataset.go)));
  document.getElementById("menu-btn").addEventListener("click", () => document.getElementById("sidebar").classList.toggle("open"));

  for (const name of FEATURE_NAMES) {
    const input = document.getElementById(name);
    const out = document.getElementById(`${name}_val`);
    input.addEventListener("input", () => { out.textContent = input.value; });
  }

  document.getElementById("diagnose-btn").addEventListener("click", diagnose);
  document.getElementById("listen-btn").addEventListener("click", speakResult);
  document.getElementById("weather-btn").addEventListener("click", checkWeather);

  renderFilters();
  renderKnowledge();
  document.getElementById("plant-search").addEventListener("input", (e) => { searchQuery = e.target.value; renderKnowledge(); });

  initAssistant();

  const hash = (location.hash || "#home").replace("#", "");
  if (document.getElementById(hash)) showSection(hash);
}

setup();
loadModel();
