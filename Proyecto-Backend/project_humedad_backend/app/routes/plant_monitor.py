from app.services.whatsapp_service import send_whatsapp_message

HUMIDITY_THRESHOULD = 30 

def check_plan(humidity,phone_number):
    if humidity < HUMIDITY_THRESHOULD:
        message="⚠️ tu planta necesita agua, nivel de humedad baja"
        send_whatsapp_message(phone_number,message)
        return True
    return False

