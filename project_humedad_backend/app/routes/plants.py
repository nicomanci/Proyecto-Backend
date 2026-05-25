from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from app import db
from app.models.schemas import plant_schema
from app.services.ml_service import get_plant_recommendations

plants_bp = Blueprint('plants', __name__)


def serialize_plant(p):
    p['_id'] = str(p['_id'])
    p['user_id'] = str(p['user_id'])
    if p.get('last_watered'):
        p['last_watered'] = p['last_watered'].isoformat()
    p['created_at'] = p['created_at'].isoformat()
    p['updated_at'] = p['updated_at'].isoformat()
    return p


@plants_bp.route('/', methods=['GET'])
@jwt_required()
def get_plants():
    user_id = get_jwt_identity()
    plants = list(db.plants.find({"user_id": ObjectId(user_id), "active": True}))

    # Enrich with last humidity reading
    for plant in plants:
        last_reading = db.sensor_readings.find_one(
            {"plant_id": plant['_id']},
            sort=[("timestamp", -1)]
        )
        plant['current_humidity'] = last_reading['humidity'] if last_reading else None
        plant['last_reading_at'] = last_reading['timestamp'].isoformat() if last_reading else None
        plant['status'] = _get_status(plant, plant['current_humidity'])

    return jsonify([serialize_plant(p) for p in plants]), 200


@plants_bp.route('/<plant_id>', methods=['GET'])
@jwt_required()
def get_plant(plant_id):
    user_id = get_jwt_identity()
    plant = db.plants.find_one({"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)})
    if not plant:
        return jsonify({"error": "Planta no encontrada"}), 404

    # Last 50 readings for history chart
    readings = list(db.sensor_readings.find(
        {"plant_id": ObjectId(plant_id)},
        sort=[("timestamp", -1)],
        limit=50
    ))
    plant['history'] = [
        {"humidity": r['humidity'], "temperature": r.get('temperature'),
         "timestamp": r['timestamp'].isoformat()}
        for r in reversed(readings)
    ]
    last = readings[0] if readings else None
    plant['current_humidity'] = last['humidity'] if last else None
    plant['status'] = _get_status(plant, plant['current_humidity'])

    return jsonify(serialize_plant(plant)), 200


@plants_bp.route('/', methods=['POST'])
@jwt_required()
def create_plant():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data.get('name'):
        return jsonify({"error": "El nombre es requerido"}), 400

    plant = plant_schema(user_id, data)
    result = db.plants.insert_one(plant)
    plant['_id'] = result.inserted_id

    return jsonify(serialize_plant(plant)), 201


@plants_bp.route('/<plant_id>', methods=['PUT'])
@jwt_required()
def update_plant(plant_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    allowed = ['name', 'scientific_name', 'plant_type', 'ideal_humidity_min',
               'ideal_humidity_max', 'watering_frequency_days', 'location',
               'photo_url', 'notes', 'sensor_id', 'last_watered']
    update_data = {k: v for k, v in data.items() if k in allowed}
    update_data['updated_at'] = datetime.utcnow()

    result = db.plants.update_one(
        {"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Planta no encontrada"}), 404

    plant = db.plants.find_one({"_id": ObjectId(plant_id)})
    return jsonify(serialize_plant(plant)), 200


@plants_bp.route('/<plant_id>', methods=['DELETE'])
@jwt_required()
def delete_plant(plant_id):
    user_id = get_jwt_identity()
    result = db.plants.update_one(
        {"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)},
        {"$set": {"active": False, "updated_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Planta no encontrada"}), 404
    return jsonify({"message": "Planta eliminada"}), 200


@plants_bp.route('/<plant_id>/water', methods=['POST'])
@jwt_required()
def log_watering(plant_id):
    """Manually log a watering event."""
    user_id = get_jwt_identity()
    now = datetime.utcnow()
    db.plants.update_one(
        {"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)},
        {"$set": {"last_watered": now, "updated_at": now}}
    )
    # Resolve active alerts for this plant
    db.alerts.update_many(
        {"plant_id": ObjectId(plant_id), "resolved": False},
        {"$set": {"resolved": True, "resolved_at": now}}
    )
    return jsonify({"message": "Riego registrado", "watered_at": now.isoformat()}), 200


@plants_bp.route('/<plant_id>/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations(plant_id):
    user_id = get_jwt_identity()
    plant = db.plants.find_one({"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)})
    if not plant:
        return jsonify({"error": "Planta no encontrada"}), 404

    readings = list(db.sensor_readings.find(
        {"plant_id": ObjectId(plant_id)},
        sort=[("timestamp", -1)], limit=100
    ))
    recs = get_plant_recommendations(plant, readings)
    return jsonify(recs), 200


def _get_status(plant, humidity):
    if humidity is None:
        return "sin_datos"
    if humidity <= plant.get('ideal_humidity_min', 40) * 0.4:
        return "critica"
    if humidity <= plant.get('ideal_humidity_min', 40):
        return "baja"
    return "normal"
