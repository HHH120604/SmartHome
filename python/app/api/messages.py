import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.sensor_data import AlertLog

router = APIRouter()
default = datetime.datetime(2025, 9, 4, 12)
time = {
    "fire": default,
    "gas": default,
    "temp": default,
    "human": default,
    "time": datetime.datetime.now(),
}
def get_log_info():
    global time
    return time

def update_log(log):
    global time
    time = log
    return

@router.get("/")
async def get_messages(
    db: Session = Depends(get_db)
):
    log = get_log_info()
    # print(log_time)
    alerts = db.query(AlertLog).filter(AlertLog.created_at > log["time"]).all()
    log["time"] = datetime.datetime.now()
    messages = []
    for message in alerts:
        print(message.alert_type)
        if (log["time"] - log[message.alert_type]).total_seconds() > 60:
            messages.append(
                {
                    "id": message.id,
                    "type": message.alert_type,
                    "content": message.message,
                    "time": log["time"]
                }
            )
            log[message.alert_type] = log["time"]
    update_log(log)
    return messages