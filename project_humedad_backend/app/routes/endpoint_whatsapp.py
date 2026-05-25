from flask import Blueprint, request,jsonify
from app.sensors.plant_monitor import check_plant

main = Blueprint("main",__name__)

@main.route("/check-plant",methods=["POST"])
def check():
    data=request.json
    humidity = data.get("humidity")
    phone = data.get("phone")
    
    alert = check_plant(humidity,phone)
    
    return jsonify({
        "alert_send": alert
    })