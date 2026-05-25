from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from app import db
from app.services.ml_service import get_plant_recommendations

rec_bp = Blueprint('recommendations', __name__)


@rec_bp.route('/<plant_id>', methods=['GET'])
@jwt_required()
def get_recommendations(plant_id):
    user_id = get_jwt_identity()
    plant = db.plants.find_one({"_id": ObjectId(plant_id), "user_id": ObjectId(user_id)})
    if not plant:
        return jsonify({"error": "Planta no encontrada"}), 404

    readings = list(db.sensor_readings.find(
        {"plant_id": ObjectId(plant_id)},
        sort=[("timestamp", -1)], limit=200
    ))
    recs = get_plant_recommendations(plant, readings)
    return jsonify(recs), 200
