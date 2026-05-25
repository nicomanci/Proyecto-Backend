from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from pymongo import MongoClient
from .config import Config

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
jwt = JWTManager()
mongo_client = None
db = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    jwt.init_app(app)
    socketio.init_app(app)

    # MongoDB
    global mongo_client, db
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client[app.config['MONGO_DB_NAME']]

    # Blueprints
    from .routes.auth import auth_bp
    from .routes.plants import plants_bp
    from .routes.sensors import sensors_bp
    from .routes.alerts import alerts_bp
    from .routes.recommendations import rec_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(plants_bp, url_prefix='/api/plants')
    app.register_blueprint(sensors_bp, url_prefix='/api/sensors')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(rec_bp, url_prefix='/api/recommendations')

    # Socket events
    from .sockets import events  # noqa

    return app
