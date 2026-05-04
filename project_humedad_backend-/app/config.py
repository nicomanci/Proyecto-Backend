import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRES_HOURS', 24)))

    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'plantwatch')

    # Push notifications (Expo)
    EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'

    # MQTT (optional)
    MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
    MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
    MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'plantwatch/sensors')

    # Thresholds
    LOW_HUMIDITY_THRESHOLD = float(os.getenv('LOW_HUMIDITY_THRESHOLD', 30.0))
    CRITICAL_HUMIDITY_THRESHOLD = float(os.getenv('CRITICAL_HUMIDITY_THRESHOLD', 15.0))
