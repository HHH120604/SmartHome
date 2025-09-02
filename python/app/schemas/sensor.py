from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SensorDataCreate(BaseModel):
    device_id: str = Field(..., description="设备ID")
    temperature: Optional[float] = Field(None, description="温度")
    humidity: Optional[float] = Field(None, description="湿度")
    light_intensity: Optional[float] = Field(None, description="光照强度")
    gas_level: Optional[float] = Field(None, description="可燃气体浓度")
    flame_detected: bool = Field(False, description="是否检测到火焰")
    soil_moisture: Optional[float] = Field(None, description="土壤湿度")
    data_json: Optional[Dict[str, Any]] = Field(None, description="其他数据")


class SensorDataResponse(BaseModel):
    id: int
    device_id: str
    house_id: int
    temperature: Optional[float]
    humidity: Optional[float]
    light_intensity: Optional[float]
    gas_level: Optional[float]
    flame_detected: bool
    soil_moisture: Optional[float]
    timestamp: datetime

    class Config:
        from_attributes = True


class EnvironmentSummary(BaseModel):
    temperature: Optional[float] = Field(None, description="当前温度")
    humidity: Optional[float] = Field(None, description="当前湿度")
    light_intensity: Optional[float] = Field(None, description="当前光照")
    safety_status: str = Field(..., description="安全状态")
    gas_level: Optional[float] = Field(None, description="气体浓度")
    last_update: Optional[datetime] = Field(None, description="最后更新时间")


class AlertCreate(BaseModel):
    device_id: str = Field(..., description="设备ID")
    alert_type: str = Field(..., description="警报类型")
    message: str = Field(..., description="警报消息")
    severity: str = Field("medium", description="严重程度")


class AlertResponse(BaseModel):
    id: int
    device_id: str
    alert_type: str
    message: str
    severity: str
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SensorHistoryQuery(BaseModel):
    hours: int = Field(24, description="获取多少小时内的数据", ge=1, le=720)
    device_id: Optional[str] = Field(None, description="特定设备ID")