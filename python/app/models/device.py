from sqlalchemy import Column, Integer, String, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    device_type = Column(String(50), nullable=False)  # light, fan, air, sensor等
    device_id = Column(String(50), unique=True, nullable=False)  # 硬件设备唯一标识
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=True)
    house_id = Column(Integer, nullable=False, default=1)
    status = Column(JSON, nullable=True)  # 存储设备当前状态
    is_online = Column(Boolean, default=False)
    module = Column(Integer, nullable=True)
    device = Column(Integer, nullable=True)
    description = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    house_id = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=func.now())