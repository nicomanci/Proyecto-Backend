import requests
import logging

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = 'https://exp.host/--/api/v2/push/send'


def send_push_notification(expo_token: str, title: str, body: str, data: dict = None):
    """
    Send push notification via Expo Push API.
    Works for both iOS and Android via React Native Expo app.
    """
    if not expo_token or not expo_token.startswith('ExponentPushToken'):
        logger.warning(f"Invalid Expo token: {expo_token}")
        return False

    payload = {
        "to": expo_token,
        "title": title,
        "body": body,
        "sound": "default",
        "badge": 1,
        "data": data or {}
    }

    try:
        response = requests.post(
            EXPO_PUSH_URL,
            json=payload,
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        result = response.json()
        if result.get('data', {}).get('status') == 'error':
            logger.error(f"Push error: {result['data'].get('message')}")
            return False
        return True
    except Exception as e:
        logger.error(f"Push notification failed: {e}")
        return False


def send_bulk_push(tokens: list, title: str, body: str, data: dict = None):
    """Send to multiple tokens at once."""
    results = []
    for token in tokens:
        ok = send_push_notification(token, title, body, data)
        results.append({"token": token, "success": ok})
    return results
