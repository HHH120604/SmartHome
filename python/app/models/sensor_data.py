from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, JSON
from sqlalchemy.sql import func
from app.database import Base


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=False)
    house_id = Column(Integer, nullable=False, default=1)
    temperature = Column(Float, nullable=True)  # 温度
    humidity = Column(Float, nullable=True)  # 湿度
    human_detected = Column(Integer, nullable=True)  # 人体检测
    light_intensity = Column(Integer, nullable=True)  # 光照强度
    gas_level = Column(Float, nullable=True)  # 可燃气体浓度
    flame_detected = Column(Boolean, default=False)  # 是否检测到火焰
    soil_moisture = Column(Float, nullable=True)  # 土壤湿度（植物养护）
    data_json = Column(JSON, nullable=True)  # 其他传感器数据
    timestamp = Column(DateTime, default=datetime.now())


class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    house_id = Column(Integer, nullable=False, default=1)
    device_id = Column(String(100), nullable=False)
    alert_type = Column(String(50), nullable=False)  # fire, gas, temperature等
    message = Column(String(500), nullable=False)  # 警报消息
    severity = Column(String(20), default="medium")  # high, medium, low
    is_resolved = Column(Boolean, default=False)  # 是否已解决
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime, nullable=True)