"""
ML Service for PlantWatch.

Phase 1 (MVP): Heuristic rule-based recommendations using plant type + history.
Phase 2: TensorFlow model trained on historical watering data.

The model predicts:
  - ideal humidity range adjustment
  - recommended watering frequency
  - care tips

This file is structured so Phase 2 can replace Phase 1 transparently.
"""
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# PHASE 1: Heuristic knowledge base
# ─────────────────────────────────────────────

PLANT_TYPE_RULES = {
    "succulent": {
        "humidity_min": 10, "humidity_max": 30,
        "watering_days": 14,
        "tips": ["Usa sustrato con buen drenaje", "Evita el riego excesivo", "Necesita mucha luz solar"]
    },
    "cactus": {
        "humidity_min": 5, "humidity_max": 20,
        "watering_days": 21,
        "tips": ["Riego muy escaso", "Alta tolerancia a la sequía", "Luz directa"]
    },
    "tropical": {
        "humidity_min": 50, "humidity_max": 80,
        "watering_days": 2,
        "tips": ["Mantén la tierra húmeda pero no encharcada", "Alta humedad ambiental", "Luz indirecta"]
    },
    "fern": {
        "humidity_min": 60, "humidity_max": 80,
        "watering_days": 2,
        "tips": ["Nunca dejes que se seque", "Nebuliza las hojas", "Sombra o luz tenue"]
    },
    "herb": {
        "humidity_min": 40, "humidity_max": 60,
        "watering_days": 3,
        "tips": ["Riego moderado y constante", "Buena ventilación", "Luz solar directa varias horas"]
    },
    "flowering": {
        "humidity_min": 40, "humidity_max": 65,
        "watering_days": 3,
        "tips": ["Riego regular", "Fertiliza durante la floración", "Luz brillante indirecta"]
    },
    "default": {
        "humidity_min": 40, "humidity_max": 70,
        "watering_days": 3,
        "tips": ["Mantén un riego regular", "Revisa el suelo antes de regar", "Luz moderada"]
    }
}


def get_plant_recommendations(plant: dict, readings: list) -> dict:
    """
    Main recommendation function.
    Uses heuristics now, will delegate to TF model in Phase 2.
    """
    plant_type = plant.get('plant_type', 'default').lower()
    rules = PLANT_TYPE_RULES.get(plant_type, PLANT_TYPE_RULES['default'])

    # Analyze historical readings
    history_analysis = _analyze_history(readings)

    # Adjust watering frequency based on history
    adjusted_frequency = _adjust_frequency(rules['watering_days'], history_analysis)

    # Build recommendations
    recs = {
        "source": "heuristic",  # Will be "tensorflow" in Phase 2
        "plant_type": plant_type,
        "ideal_humidity": {
            "min": rules['humidity_min'],
            "max": rules['humidity_max'],
            "current": history_analysis.get('avg_humidity')
        },
        "watering": {
            "recommended_every_days": adjusted_frequency,
            "last_watered": plant.get('last_watered').isoformat() if plant.get('last_watered') else None,
        },
        "tips": rules['tips'],
        "history_summary": history_analysis,
        "health_score": _calculate_health_score(plant, history_analysis, rules)
    }

    return recs


def _analyze_history(readings: list) -> dict:
    if not readings:
        return {"data_points": 0, "avg_humidity": None, "min_humidity": None,
                "max_humidity": None, "trend": "unknown"}

    humidities = [r['humidity'] for r in readings]
    return {
        "data_points": len(humidities),
        "avg_humidity": round(float(np.mean(humidities)), 1),
        "min_humidity": round(float(np.min(humidities)), 1),
        "max_humidity": round(float(np.max(humidities)), 1),
        "trend": _calculate_trend(humidities)
    }


def _calculate_trend(values: list) -> str:
    if len(values) < 5:
        return "insufficient_data"
    recent = np.mean(values[:10])
    older = np.mean(values[-10:])
    diff = recent - older
    if diff < -5:
        return "decreasing"
    elif diff > 5:
        return "increasing"
    return "stable"


def _adjust_frequency(base_days: int, history: dict) -> int:
    """Adjust watering frequency based on observed drying rate."""
    if history.get('trend') == 'decreasing' and history.get('avg_humidity', 50) < 30:
        return max(1, base_days - 1)
    if history.get('trend') == 'increasing':
        return base_days + 1
    return base_days


def _calculate_health_score(plant: dict, history: dict, rules: dict) -> dict:
    """Return a 0-100 health score with label."""
    avg = history.get('avg_humidity')
    if avg is None:
        return {"score": None, "label": "Sin datos"}

    ideal_min = rules['humidity_min']
    ideal_max = rules['humidity_max']

    if ideal_min <= avg <= ideal_max:
        score = 95
        label = "Excelente"
    elif avg < ideal_min:
        deficit = ideal_min - avg
        score = max(10, 95 - (deficit * 2))
        label = "Necesita agua" if deficit < 20 else "Crítica"
    else:
        excess = avg - ideal_max
        score = max(40, 95 - excess)
        label = "Exceso de humedad"

    return {"score": round(score), "label": label}


# ─────────────────────────────────────────────
# PHASE 2: TensorFlow model (placeholder)
# ─────────────────────────────────────────────

def load_tf_model():
    """
    Load TensorFlow model for Phase 2.
    Uncomment when model is trained.
    """
    # import tensorflow as tf
    # model = tf.keras.models.load_model('app/ml/models/plant_model.h5')
    # return model
    return None


def predict_with_tf(model, features: np.ndarray):
    """
    Phase 2: Use trained TF model.
    Input features: [plant_type_encoded, avg_humidity, temp, hour_of_day, days_since_watered]
    Output: [humidity_min, humidity_max, watering_days]
    """
    # prediction = model.predict(features.reshape(1, -1))
    # return prediction[0]
    pass
