from datetime import datetime, timedelta
from bson import ObjectId
from app import db
from app.models.schemas import alert_schema
from app.services.push_service import send_push_notification
from flask import current_app


def process_humidity_alert(plant, humidity):
    """
    Check humidity against thresholds.
    Returns alert dict if triggered, else None.
    """
    min_h = plant.get('ideal_humidity_min', 40)
    critical_threshold = min_h * 0.4
    low_threshold = min_h

    alert_type = None
    message = None

    if humidity <= critical_threshold:
        alert_type = "critical_humidity"
        message = f"⚠️ {plant['name']} está en estado CRÍTICO ({humidity:.0f}% humedad). ¡Riega inmediatamente!"
    elif humidity <= low_threshold:
        alert_type = "low_humidity"
        message = f"💧 {plant['name']} necesita agua ({humidity:.0f}% humedad)"

    if not alert_type:
        return None

    # Avoid duplicate alerts: don't create if same type in last 30 min
    recent = db.alerts.find_one({
        "plant_id": plant['_id'],
        "alert_type": alert_type,
        "resolved": False,
        "created_at": {"$gte": datetime.utcnow() - timedelta(minutes=30)}
    })
    if recent:
        return None

    # Create alert
    new_alert = alert_schema(
        str(plant['user_id']),
        str(plant['_id']),
        plant['name'],
        alert_type,
        humidity,
        message
    )
    result = db.alerts.insert_one(new_alert)
    new_alert['_id'] = str(result.inserted_id)

    # Send push notification
    user = db.users.find_one({"_id": plant['user_id']})
    if user and user.get('push_tokens'):
        for token in user['push_tokens']:
            send_push_notification(token, "PlantWatch 🌱", message)
        db.alerts.update_one(
            {"_id": result.inserted_id},
            {"$set": {"push_sent": True}}
        )

    return {
        "id": new_alert['_id'],
        "type": alert_type,
        "message": message
    }
