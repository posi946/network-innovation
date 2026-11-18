import random
from typing import List, Tuple

FEATURE_NAMES = ["soil_moisture", "temperature_c", "light_level", "humidity"]
LABELS = ["Healthy", "Needs Water", "Overwatered Risk", "Heat/Light Stress"]

# Approximate healthy ranges used for data generation and assistant reasoning
HEALTHY_RANGES = {
    "soil_moisture": (35, 65),
    "temperature_c": (18, 29),
    "light_level": (35, 75),
    "humidity": (35, 70),
}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def generate_sample(rng: random.Random) -> Tuple[List[float], int]:
    """Generate one synthetic sensor reading and its plant status label.

    The rules are intentionally a bit fuzzy/noisy so a neural network has a
    meaningful pattern to learn instead of a trivial threshold.
    """
    soil = rng.uniform(0, 100)
    temp = rng.uniform(10, 40)
    light = rng.uniform(0, 100)
    hum = rng.uniform(20, 90)

    # Base scores for each condition; highest score becomes the label.
    needs_water = max(0.0, (35 - soil) / 35) + rng.uniform(-0.08, 0.08)
    overwatered = max(0.0, (soil - 70) / 30) + rng.uniform(-0.08, 0.08)

    heat_stress = 0.0
    if temp > 30:
        heat_stress += (temp - 30) / 10
    if temp < 15:
        heat_stress += (15 - temp) / 5
    if light > 85:
        heat_stress += (light - 85) / 15
    if light < 20:
        heat_stress += (20 - light) / 20
    if hum < 30:
        heat_stress += (30 - hum) / 40
    heat_stress += rng.uniform(-0.08, 0.08)

    scores = [0.35 + rng.uniform(-0.05, 0.05), needs_water, overwatered, heat_stress]
    label = max(range(len(scores)), key=lambda i: scores[i])

    # Add measurement noise
    soil = _clamp(soil + rng.uniform(-2, 2), 0, 100)
    temp = _clamp(temp + rng.uniform(-0.7, 0.7), 5, 45)
    light = _clamp(light + rng.uniform(-3, 3), 0, 100)
    hum = _clamp(hum + rng.uniform(-2, 2), 10, 100)

    return [soil, temp, light, hum], label


def make_dataset(n: int, seed: int = 42) -> Tuple[List[List[float]], List[int]]:
    rng = random.Random(seed)
    X, y = [], []
    for _ in range(n):
        features, label = generate_sample(rng)
        X.append(features)
        y.append(label)
    return X, y


def normalize_features(X: List[List[float]]) -> List[List[float]]:
    """Scale features to roughly [0, 1] using known sensor bounds."""
    bounds = [(0, 100), (5, 45), (0, 100), (10, 100)]
    out = []
    for row in X:
        norm = []
        for value, (lo, hi) in zip(row, bounds):
            norm.append((value - lo) / (hi - lo))
        out.append(norm)
    return out


def one_hot(labels: List[int], num_classes: int) -> List[List[float]]:
    encoded = []
    for label in labels:
        row = [0.0] * num_classes
        row[label] = 1.0
        encoded.append(row)
    return encoded


def train_test_split(
    X: List[List[float]], y: List[int], test_ratio: float = 0.2, seed: int = 42
) -> Tuple[List[List[float]], List[int], List[List[float]], List[int]]:
    rng = random.Random(seed)
    indices = list(range(len(X)))
    rng.shuffle(indices)
    split = int(len(X) * (1 - test_ratio))
    train_idx, test_idx = indices[:split], indices[split:]
    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    return X_train, y_train, X_test, y_test
