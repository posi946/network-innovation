# PlantGuard (network-innovation)

PlantGuard is an intelligent, lightweight plant and farm knowledge network that combines a **browser-based neural network**, **weather-aware guidance**, an **extensive plant & weed encyclopedia**, and a **local conversational assistant** in a wide, dynamic chamomile-themed web experience.

Given four inputs — soil moisture, temperature, light exposure, and humidity — the neural model predicts:
- **Healthy**
- **Needs Water**
- **Overwatered Risk**
- **Heat/Light Stress**

The app runs as a static site: neural inference, search, and the assistant run client-side in the browser (no backend or external AI API key required).

> Note: Training data is synthetic and intended to demonstrate the approach. For real-world deployment, train/calibrate with real sensor data for specific plant species.

## Web app features
- **Plant Diagnosis:** Neural assessment (4→12→4 feedforward model, loaded from `model_weights.json`) with confidence, prioritized recommendations, and optional spoken summary (browser speech synthesis, where supported).
- **Weather Insights:** Location-based current conditions via [Open-Meteo](https://open-meteo.com/) (no API key) with practical operational guidance (permission/connectivity required).
- **Encyclopedia (Knowledge Network):** **82 structured entries** spanning crops, vegetables, fruits, legumes, tubers, herbs, trees/special plants, and **weeds**. Each entry includes lifespan/cycle, conditions, vulnerabilities/weaknesses, management/control, impact/use, and notes, with category filters and search.
- **3D experience:** Clearly visible 3D hero depth/motion, depth-styled surfaces, **realistic 3D hover/tilt effects** on cards (including encyclopedia results), and a **3D phone-like spin animation** when encyclopedia results update from search/filter (respects `prefers-reduced-motion`).
- **Assistant:** Built-in local assistant that can explain the latest diagnosis, interpret available weather context, and answer questions from the encyclopedia/app context.
- **Chamomile Botanical Guide:** Integrated informational section (origin & habitat, varieties, classic records, brewing methods, dosage & cautions, products & processing, and presentation grades) in the Natura Care style.
- **Lex · Core Link:** DocuSense Africa v2 voice companion built directly into PlantGuard from the 15 build prompts — animated colour-themed orb, wake word detection, Web Speech STT/TTS, intent parsing, settings for companion name/colour/voice/language, and analysis/document command flows.
- **Design & accessibility:** Wide, dynamic chamomile palette (green-forward), **light/dark mode** with sun/moon toggle and saved preference, responsive layout, and motion/accessibility considerations.

## Project structure
```text
.
├── index.html          # Web app UI and sections
├── styles.css          # Chamomile theme, layout, 3D/hover/spin styles, light/dark modes
├── app.js              # Browser NN inference, diagnosis, weather, encyclopedia, assistant, UI/3D behavior
├── knowledge.js        # Knowledge network dataset (82 plants, weeds, herbs, special species)
├── model_weights.json  # Trained neural network weights for browser inference
├── main.py             # CLI entrypoint
├── plantguard/         # Python package (CLI/assistant/data/model)
│   ├── __init__.py
│   ├── assistant.py
│   ├── cli.py
│   ├── data.py
│   └── model.py
├── docusense/            # DocuSense build implemented from the 15 prompts
│   ├── frontend/         # Lex orb, voice loop, settings and styles (inside PlantGuard)
│   ├── backend/          # FastAPI API, security, RAG, auth, routers and tests
│   └── migrations/       # Initial SQL schema with RLS and pgvector
├── tests/
│   └── test_plantguard.py
├── requirements.txt
├── LICENSE
└── README.md
```

## Run the web app locally
```bash
cd network-innovation
python3 -m http.server 8765
# open http://localhost:8765
```
You can use any static file server/port (e.g. `8080`). For full functionality, allow location access when using Weather Insights.

## Run the DocuSense API (optional)
```bash
cd docusense/backend
pip install -r requirements.txt
cp .env.example .env   # fill in the keys you have; offline demo mode works without them
uvicorn app.main:app --reload --port 8000
```
Point the browser UI at the API with `window.DOCUSENSE_API_URL = "http://localhost:8000"` before `lex.js` loads. Without it, Lex runs in a deterministic local demo mode.

## Deploy
Deploy as a static site (e.g. Vercel) from the repository root. The browser app loads `model_weights.json`, `knowledge.js`, and runs inference/UI logic client-side.

## Python CLI (optional)
Requires Python 3.10+ (standard library only).

```bash
# Demo
python3 main.py demo

# Train
python3 main.py train --samples 2000 --epochs 300

# Predict: soil_moisture temperature_c light_level humidity
python3 main.py predict 22 28 70 40
```

## How it works
1. **Data generation (`plantguard/data.py`)** creates labeled synthetic sensor readings with realistic, slightly noisy rules.
2. **Neural network (`plantguard/model.py`)** is a small MLP (`input -> ReLU hidden -> softmax`) trained with backpropagation and cross-entropy loss.
3. **Browser app (`app.js`)** performs local inference, renders guidance, weather context, encyclopedia search, and assistant responses from built-in knowledge/context.
4. **CLI assistant (`plantguard/assistant.py`)** interprets predictions with raw readings for human-friendly CLI guidance.

## Tests
```bash
python3 -m unittest discover -s tests -v
```

## License
MIT
