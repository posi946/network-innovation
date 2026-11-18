# PlantGuard (network-innovation)

PlantGuard is an innovative, lightweight Python project that combines a **neural network** with a **built-in smart care assistant** to diagnose plant stress from sensor-like readings.

Given four inputs — soil moisture, temperature, light level, and humidity — PlantGuard predicts whether a plant is:
- **Healthy**
- **Needs Water**
- **Overwatered Risk**
- **Heat/Light Stress**

It then generates an explainable, AI-style care report with observations and recommended actions.

## Why this is innovative
Most simple plant reminders use fixed thresholds only. PlantGuard adds a learned layer:

- **Neural network diagnosis:** A feedforward neural network (implemented from scratch in pure Python) learns patterns from synthetic sensor data where conditions can overlap and be noisy.
- **Integrated AI assistant:** Model predictions are combined with context-aware reasoning (range analysis, confidence-aware guidance, prioritized tips) to produce actionable advice.
- **Runs locally:** No external APIs or API keys required; uses only the Python standard library.

> Note: Training data is synthetic and intended to demonstrate the approach. For real-world deployment, train/calibrate with real sensor data for specific plant species.

## Project structure
```text
.
├── main.py
├── plantguard/
│   ├── __init__.py
│   ├── assistant.py   # built-in smart care assistant
│   ├── cli.py         # command-line interface
│   ├── data.py        # synthetic data generation & preprocessing
│   └── model.py       # neural network (from scratch)
└── tests/
    └── test_plantguard.py
```

## Requirements
- Python 3.10+ (tested with modern Python 3.x)
- No third-party packages required

## Usage

### Web app (browser)
Open `index.html` locally or deploy the repo as a static site (e.g. on Vercel). The browser app loads `model_weights.json` and runs the neural network + built-in care assistant client-side.

### 1) Run the CLI demo
Trains a quick model (if no saved weights exist) and prints diagnoses for sample scenarios:

```bash
python3 main.py demo
```

### 2) Train a model
```bash
python3 main.py train --samples 2000 --epochs 300
```

This saves weights to `model_weights.json` by default.

### 3) Predict from your own readings (CLI)
Provide values in this order: `soil_moisture temperature_c light_level humidity`

```bash
python3 main.py predict 22 28 70 40
```

Example output includes:
- predicted status and confidence
- sensor observations vs healthy ranges
- recommended care actions
- class probabilities from the neural network

## How it works
1. **Data generation (`plantguard/data.py`)** creates labeled synthetic sensor readings with realistic, slightly noisy rules.
2. **Neural network (`plantguard/model.py`)** is a small MLP (`input -> ReLU hidden -> softmax`) trained with backpropagation and cross-entropy loss.
3. **Assistant (`plantguard/assistant.py`)** interprets the prediction together with the raw readings to produce human-friendly guidance.

## Tests
```bash
python3 -m unittest discover -s tests -v
```

## License
MIT
