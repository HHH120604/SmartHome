from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class DeviceCreate(BaseModel):
    name: str = Field(..., description="设备名称")
    device_type: str = Field(..., description="设备类型")
    room_id: Optional[int] = Field(None, description="房间ID")


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="设备名称")
    room_id: Optional[int] = Field(None, description="房间ID")
    is_online: Optional[bool] = Field(None, description="是否在线")


class DeviceControl(BaseModel):
    device_id: int = Field(..., description="设备id")
    status: Dict[str, Any] = Field(..., description="设备状态")


class DeviceResponse(BaseModel):
    id: int
    type: str
    name: str
    on: bool
    status: Optional[Dict[str, Any]]
    scene: str
    online: bool
    desc: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str = Field(..., description="房间名称")


class RoomResponse(BaseModel):
    id: int
    name: str
    house_id: int
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True


class DeviceStatusUpdate(BaseModel):
    device_id: str = Field(..., description="设备ID")
    status: Dict[str, Any] = Field(..., description="设备状态")
    is_online: bool = Field(True, description="是否在线")