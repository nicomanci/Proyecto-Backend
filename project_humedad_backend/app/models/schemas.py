from datetime import datetime
from bson import ObjectId


def user_schema(name, email, hashed_password):
    return {
        "name": name,
        "email": email,
        "password": hashed_password,
        "push_tokens": [],         # Expo push tokens
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def plant_schema(user_id, data):
    return {
        "user_id": ObjectId(user_id),
        "name": data.get("name"),
        "scientific_name": data.get("scientific_name", ""),
        "plant_type": data.get("plant_type", ""),       # succulent, tropical, etc.
        "ideal_humidity_min": float(data.get("ideal_humidity_min", 40)),
        "ideal_humidity_max": float(data.get("ideal_humidity_max", 70)),
        "watering_frequency_days": int(data.get("watering_frequency_days", 3)),
        "location": data.get("location", ""),
        "photo_url": data.get("photo_url", ""),
        "notes": data.get("notes", ""),
        "sensor_id": data.get("sensor_id", None),       # Arduino sensor ID
        "active": True,
        "last_watered": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


def sensor_reading_schema(plant_id, sensor_id, humidity, temperature=None):
    return {
        "plant_id": ObjectId(plant_id),
        "sensor_id": sensor_id,
        "humidity": float(humidity),
        "temperature": float(temperature) if temperature else None,
        "timestamp": datetime.utcnow()
    }


def alert_schema(user_id, plant_id, plant_name, alert_type, humidity, message):
    return {
        "user_id": ObjectId(user_id),
        "plant_id": ObjectId(plant_id),
        "plant_name": plant_name,
        "alert_type": alert_type,               # "low_humidity" | "critical_humidity"
        "humidity_at_alert": float(humidity),
        "message": message,
        "resolved": False,
        "push_sent": False,
        "created_at": datetime.utcnow(),
        "resolved_at": None
    }
