import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.database import init_db, get_db
from app.models.device import Device, Room

engine = create_engine(
    "sqlite:///./python/data/hongmeng.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
init_db()
db = SessionLocal()

rooms = [
    Room(
        name="主卧",
        house_id=1,
    ),
    Room(
        name="客卧",
        house_id=1,
    ),
    Room(
        name="客厅",
        house_id=1,
    ),
    Room(
        name="卫生间",
        house_id=1,
    ),
]

devices = [
    Device(
        name="主卧室灯",
        device_type="light",
        device_id=f"light_{random.randint(1, 99999):05d}",
        room_id=1,
        house_id=1,
        status={"power": False},  # 默认状态
        is_online=True,
        description="已关闭",
    ),
    Device(
        name="客卧室灯",
        device_type="light",
        device_id=f"light_{random.randint(1, 99999):05d}",
        room_id=2,
        house_id=1,
        status={"power": False},  # 默认状态
        is_online=True,
        description="已关闭",
    ),
    Device(
        name="客厅空调",
        device_type="airconditioner",
        device_id=f"airconditioner_{random.randint(1, 99999):05d}",
        room_id=3,
        house_id=1,
        status={"power": False, "mode": "cool", "temp": 26},  # 默认状态
        is_online=True,
        description="已关闭",
    ),
    Device(
        name="卫生间热水器",
        device_type="shower",
        device_id=f"shower_{random.randint(1, 99999):05d}",
        room_id=4,
        house_id=1,
        status={"power": False, "temp": 40},  # 默认状态
        is_online=True,
        description="已关闭",
    ),
]

for room in rooms:
    db.add(room)
    db.commit()
    
for device in devices:
    db.add(device)
    db.commit()

db.close()