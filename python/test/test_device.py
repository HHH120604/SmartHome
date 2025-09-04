from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, desc, func
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import init_db, get_db
from app.models.user import User, UserRole
from app.models.device import Device, Room
from app.models.sensor_data import AlertLog, SensorData

engine = create_engine(
    "sqlite:///./python/data/hongmeng.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
init_db()
db = SessionLocal()

users = [
    User(
        username="房主",
        role=UserRole.OWNER,
        house_id=1,
    ),
]

rooms = [
    Room(
        name="全屋",
        user_id=1,
        house_id=1,
    ),
    Room(
        name="客厅",
        user_id=1,
        house_id=1,
    ),
    Room(
        name="卧室",
        user_id=1,
        house_id=1,
    ),
    Room(
        name="厨房",
        user_id=1,
        house_id=1,
    ),
    Room(
        name="卫生间",
        user_id=1,
        house_id=1,
    ),
]

devices = [
    Device(
        name="客厅音响",
        device_type="light",
        device_id=f"light_{random.randint(1, 99999):05d}",
        user_id=1,
        room_id=2,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=4,
        device=4,
        description="已关闭",
    ),
    Device(
        name = "火焰检测器",
        device_type = "sensor",
        device_id = f"sensor_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=4,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=1,
        device=0,
        description="已关闭",     
    ),
    Device(
        name = "淋浴器",
        device_type = "fan",
        device_id = f"fan_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=5,
        house_id=1,
        status={"power": False,"temp":30},
        is_online=True,
        module=7,
        device=9,
        description="已关闭",     
    ),
    Device(
        name = "智能浇花",
        device_type = "fan",
        device_id = f"fan_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=2,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=7,
        device=9,
        description="已关闭",     
    ),
    Device(
        name = "可燃气体警报器",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=4,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=2,
        device=0,
        description="已关闭",     
    ),
    Device(
        name = "厨房新风机",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=4,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=7,
        device=8,
        description="已关闭",     
    ),
    Device(
        name = "人体检测",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=2,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=6,
        device=0,
        description="已关闭",     
    ),
    Device(
        name = "客厅氛围灯",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=2,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=4,
        device=2,
        description="已关闭",     
    ),
    Device(
        name = "中央空调",
        device_type = "air",
        device_id = f"air_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=2,
        house_id=1,
        status={"power": False, "mode": "cool", "temp": 18},
        is_online=True,
        module=7,
        device=8,
        description="已关闭",     
    ),
    Device(
        name = "卧室灯",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=3,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=4,
        device=1,
        description="已关闭",     
    ),
    Device(
        name = "温湿度传感器",
        device_type = "light",
        device_id = f"light_{random.randint(1,99999):05d}",
        user_id=1,
        room_id=3,
        house_id=1,
        status={"power": False},
        is_online=True,
        module=7,
        device=0,
        description="已关闭",     
    ),
]

for user in users:
    db.add(user)
db.commit()

for room in rooms:
    db.add(room)
db.commit()
    
for device in devices:
    db.add(device)
db.commit()
# default = datetime(2025, 9, 4, 12)
# time = {
#     "fire": default,
#     "gas": default,
#     "temp": default,
#     "human": default,
#     "time": datetime(2025,9,4,13,24,50),
# }
# alerts = db.query(AlertLog).filter(AlertLog.created_at > time["time"]).all()

db.close()