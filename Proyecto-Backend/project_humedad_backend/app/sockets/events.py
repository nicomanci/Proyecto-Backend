from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from app import socketio
import logging

logger = logging.getLogger(__name__)


@socketio.on('connect')
def on_connect(auth):
    """Client connects and authenticates via token."""
    token = None
    if auth:
        token = auth.get('token')

    if not token:
        logger.warning("Socket connection without token")
        return False  # Reject connection

    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
        join_room(user_id)
        emit('connected', {'message': 'Conectado a PlantWatch en tiempo real', 'user_id': user_id})
        logger.info(f"Socket connected: user {user_id}")
    except Exception as e:
        logger.error(f"Socket auth error: {e}")
        return False


@socketio.on('disconnect')
def on_disconnect():
    logger.info("Socket client disconnected")


@socketio.on('join')
def on_join(data):
    """Allow explicit room join."""
    room = data.get('room')
    if room:
        join_room(room)
        emit('joined', {'room': room})


@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    if room:
        leave_room(room)
