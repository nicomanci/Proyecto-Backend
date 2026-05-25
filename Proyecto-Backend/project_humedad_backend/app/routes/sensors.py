from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from app import db
from app.models.schemas import sensor_reading_schema
from app.services.alert_service import process_humidity_alert

sensors_bp = Blueprint('sensors', __name__)


@sensors_bp.route('/reading', methods=['POST'])
def receive_reading():
    """
    Arduino sends data here.
    Accepts: { "sensor_id": "S1", "humidity": 45.2, "temperature": 22.1, "api_key": "..." }
    No JWT needed - uses API key auth instead for embedded devices.
    """
    data = request.get_json()

    # Simple API key auth for Arduino
    api_key = data.get('api_key') or request.headers.get('X-API-Key')
    if api_key != _get_valid_api_key():
        return jsonify({"error": "API key inválida"}), 401

    sensor_id = data.get('sensor_id')
    humidity = data.get('humidity')
    temperature = data.get('temperature')

    if sensor_id is None or humidity is None:
        return jsonify({"error": "sensor_id y humidity son requeridos"}), 400

    # Find plant assigned to this sensor
    plant = db.plants.find_one({"sensor_id": sensor_id, "active": True})
    if not plant:
        return jsonify({"message": "Sensor no asignado a ninguna planta", "sensor_id": sensor_id}), 200

    # Save reading
    reading = sensor_reading_schema(str(plant['_id']), sensor_id, humidity, temperature)
    db.sensor_readings.insert_one(reading)

    # Check thresholds and trigger alerts
    alert = process_humidity_alert(plant, humidity)

    # Emit real-time update via WebSocket
    from app import socketio
    socketio.emit('humidity_update', {
        "plant_id": str(plant['_id']),
        "sensor_id": sensor_id,
        "humidity": humidity,
        "temperature": temperature,
        "status": _get_status(plant, humidity),
        "alert": alert
    }, room=str(plant['user_id']))

    return jsonify({"message": "Lectura registrada", "plant_id": str(plant['_id'])}), 200


@sensors_bp.route('/history/<plant_id>', methods=['GET'])
@jwt_required()
def get_history(plant_id):
    user_id = get_jwt_identity()
    plant = db.plants.find_one({"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)})
    if not plant:
        return jsonify({"error": "Planta no encontrada"}), 404

    limit = int(request.args.get('limit', 100))
    readings = list(db.sensor_readings.find(
        {"plant_id": ObjectId(plant_id)},
        sort=[("timestamp", -1)],
        limit=limit
    ))
    return jsonify([{
        "humidity": r['humidity'],
        "temperature": r.get('temperature'),
        "timestamp": r['timestamp'].isoformat()
    } for r in reversed(readings)]), 200


@sensors_bp.route('/simulate', methods=['POST'])
@jwt_required()
def simulate_reading():
    """Dev only: simulate a sensor reading for testing."""
    user_id = get_jwt_identity()
    data = request.get_json()
    plant_id = data.get('plant_id')
    humidity = float(data.get('humidity', 50))
    temperature = data.get('temperature')

    plant = db.plants.find_one({"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)})
    if not plant:
        return jsonify({"error": "Planta no encontrada"}), 404

    reading = sensor_reading_schema(plant_id, plant.get('sensor_id', 'SIM'), humidity, temperature)
    db.sensor_readings.insert_one(reading)
    alert = process_humidity_alert(plant, humidity)

    from app import socketio
    socketio.emit('humidity_update', {
        "plant_id": plant_id,
        "humidity": humidity,
        "temperature": temperature,
        "status": _get_status(plant, humidity),
        "alert": alert
    }, room=str(plant['user_id']))

    return jsonify({"message": "Lectura simulada", "humidity": humidity}), 200


def _get_valid_api_key():
    import os
    return os.getenv('ARDUINO_API_KEY', 'arduino-secret-key')


def _get_status(plant, humidity):
    min_h = plant.get('ideal_humidity_min', 40)
    if humidity <= min_h * 0.4:
        return "critica"
    if humidity <= min_h:
        return "baja"
    return "normal"
