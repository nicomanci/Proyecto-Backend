from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from app import db

alerts_bp = Blueprint('alerts', __name__)


def serialize_alert(a):
    a['_id'] = str(a['_id'])
    a['user_id'] = str(a['user_id'])
    a['plant_id'] = str(a['plant_id'])
    a['created_at'] = a['created_at'].isoformat()
    if a.get('resolved_at'):
        a['resolved_at'] = a['resolved_at'].isoformat()
    return a


@alerts_bp.route('/', methods=['GET'])
@jwt_required()
def get_alerts():
    user_id = get_jwt_identity()
    resolved = request.args.get('resolved', 'false').lower() == 'true'
    alerts = list(db.alerts.find(
        {"user_id": ObjectId(user_id), "resolved": resolved},
        sort=[("created_at", -1)],
        limit=50
    ))
    return jsonify([serialize_alert(a) for a in alerts]), 200


@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alert(alert_id):
    user_id = get_jwt_identity()
    result = db.alerts.update_one(
        {"_id": ObjectId(alert_id), "user_id": ObjectId(user_id)},
        {"$set": {"resolved": True, "resolved_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        return jsonify({"error": "Alerta no encontrada"}), 404
    return jsonify({"message": "Alerta resuelta"}), 200


@alerts_bp.route('/active-count', methods=['GET'])
@jwt_required()
def get_active_count():
    user_id = get_jwt_identity()
    count = db.alerts.count_documents({"user_id": ObjectId(user_id), "resolved": False})
    return jsonify({"count": count}), 200
