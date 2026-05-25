from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.schemas import user_schema
from app.utils.validators import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not name or not email or not password:
        return jsonify({"error": "Todos los campos son requeridos"}), 400
    if not validate_email(email):
        return jsonify({"error": "Email inválido"}), 400
    if not validate_password(password):
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres"}), 400
    if db.users.find_one({"email": email}):
        return jsonify({"error": "El email ya está registrado"}), 409

    user = user_schema(name, email, generate_password_hash(password))
    result = db.users.insert_one(user)
    token = create_access_token(identity=str(result.inserted_id))

    return jsonify({
        "message": "Usuario registrado",
        "token": token,
        "user": {"id": str(result.inserted_id), "name": name, "email": email}
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = db.users.find_one({"email": email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = create_access_token(identity=str(user['_id']))
    return jsonify({
        "token": token,
        "user": {"id": str(user['_id']), "name": user['name'], "email": user['email']}
    }), 200


@auth_bp.route('/push-token', methods=['POST'])
@jwt_required()
def register_push_token():
    """Register Expo push token for notifications."""
    user_id = get_jwt_identity()
    token = request.get_json().get('token')
    if not token:
        return jsonify({"error": "Token requerido"}), 400

    db.users.update_one(
        {"_id": user_id},
        {"$addToSet": {"push_tokens": token}}
    )
    return jsonify({"message": "Token registrado"}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    from bson import ObjectId
    user = db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    user['_id'] = str(user['_id'])
    return jsonify(user), 200
