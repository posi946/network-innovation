from typing import Dict, List

from .data import FEATURE_NAMES, HEALTHY_RANGES, LABELS


def _status_for_value(name: str, value: float) -> str:
    lo, hi = HEALTHY_RANGES[name]
    if value < lo:
        return "low"
    if value > hi:
        return "high"
    return "ok"


def analyze_readings(readings: Dict[str, float]) -> List[str]:
    notes = []
    for name in FEATURE_NAMES:
        value = readings[name]
        lo, hi = HEALTHY_RANGES[name]
        status = _status_for_value(name, value)
        if status == "low":
            notes.append(f"{name.replace('_', ' ')} is low ({value:.1f}; healthy ~{lo}-{hi}).")
        elif status == "high":
            notes.append(f"{name.replace('_', ' ')} is high ({value:.1f}; healthy ~{lo}-{hi}).")
    if not notes:
        notes.append("All monitored readings are within the healthy range.")
    return notes


def recommend(label: str, readings: Dict[str, float], confidence: float) -> List[str]:
    tips: List[str] = []
    soil = readings["soil_moisture"]
    temp = readings["temperature_c"]
    light = readings["light_level"]
    hum = readings["humidity"]

    if label == "Needs Water":
        tips.append("Water the plant gradually and check that excess water can drain.")
        if hum < HEALTHY_RANGES["humidity"][0]:
            tips.append("Increase humidity slightly (mist nearby air or use a pebble tray) to reduce drying stress.")
        tips.append("Recheck soil moisture in a few hours before watering again.")
    elif label == "Overwatered Risk":
        tips.append("Pause watering and let the top soil dry before the next watering.")
        tips.append("Ensure the pot has drainage and the roots are not sitting in water.")
        if light < HEALTHY_RANGES["light_level"][0]:
            tips.append("Provide a bit more light to help the soil dry at a healthy rate.")
    elif label == "Heat/Light Stress":
        if temp > HEALTHY_RANGES["temperature_c"][1]:
            tips.append("Move the plant to a cooler spot and avoid hot afternoon sun.")
        if temp < HEALTHY_RANGES["temperature_c"][0]:
            tips.append("Move the plant away from cold drafts and keep temperature more stable.")
        if light > HEALTHY_RANGES["light_level"][1]:
            tips.append("Reduce direct light exposure or diffuse harsh light.")
        if light < HEALTHY_RANGES["light_level"][0]:
            tips.append("Increase light exposure gradually (brighter window or grow light).")
        if hum < HEALTHY_RANGES["humidity"][0]:
            tips.append("Raise humidity moderately if leaves look dry or curled.")
        if not tips:
            tips.append("Stabilize temperature, light, and humidity to reduce environmental stress.")
    else:  # Healthy
        tips.append("Keep the current care routine stable and monitor changes over time.")
        tips.append("Make small adjustments only if one reading trends out of range.")

    if confidence < 0.55:
        tips.insert(0, "Confidence is moderate—take a second reading soon to confirm before major changes.")
    return tips


def generate_report(features: List[float], probabilities: List[float]) -> str:
    readings = {name: float(value) for name, value in zip(FEATURE_NAMES, features)}
    label_index = max(range(len(probabilities)), key=lambda i: probabilities[i])
    label = LABELS[label_index]
    confidence = probabilities[label_index]

    lines = []
    lines.append("PlantGuard Diagnosis")
    lines.append("=" * 20)
    lines.append(f"Predicted status: {label} ({confidence * 100:.1f}% confidence)")
    lines.append("")
    lines.append("Sensor readings:")
    for name in FEATURE_NAMES:
        lines.append(f"- {name.replace('_', ' ')}: {readings[name]:.1f}")
    lines.append("")
    lines.append("Assistant observations:")
    for note in analyze_readings(readings):
        lines.append(f"- {note}")
    lines.append("")
    lines.append("Recommended actions:")
    for tip in recommend(label, readings, confidence):
        lines.append(f"- {tip}")
    lines.append("")
    lines.append("Model probabilities:")
    for idx, prob in enumerate(probabilities):
        lines.append(f"- {LABELS[idx]}: {prob * 100:.1f}%")
    return "\n".join(lines)
