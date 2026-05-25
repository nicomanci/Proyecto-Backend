from twilio.rest import Client
import os

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
FROM_WHATSAPP ="whatsapp:+14155238886"

client = Client(ACCOUNT_SID, AUTH_TOKEN)
def send_whatsappa_message(to,message):
    try:
        msg= client.message.create(
            body=message,
            from_=FROM_WHATSAPP,
            to=f"whatsapp:{to}"
        )
        return msg.sid
    except Exception as e:
        print(f"error enviando mensaje: {e}")
        return None