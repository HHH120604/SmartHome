from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.database import get_db
from app.models.device import Device, Room
from app.models.user import User, UserRole
from app.schemas.device import (
    DeviceResponse, DeviceControl, DeviceCreate,
    RoomCreate, RoomResponse, DeviceUpdate
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[DeviceResponse])
async def get_devices(
        room_id: int = None,
        device_type: str = None,
        # current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取设备列表"""
    query = db.query(Device, Room.name) \
        .join(Room, Device.room_id==Room.id) \
        .filter(Device.house_id == 1)

    # 访客只能看到灯光设备
    # if current_user.role == UserRole.GUEST:
    #     query = query.filter(Device.device_type == "light")

    # 筛选条件
    if room_id:
        query = query.filter(Device.room_id == room_id)
    if device_type:
        query = query.filter(Device.device_type == device_type)

    devices = [
        {
            "id": device[0].id,
            "type": device[0].device_type,
            "name": device[0].name,
            "on": device[0].status["power"],
            "status": device[0].status,
            "scene": device[1],
            "online": device[0].is_online,
            "desc": device[0].description,
        } for device in query.all()
    ]
    
    return devices


@router.post("/", response_model=DeviceResponse)
async def create_device(
        device: DeviceCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """添加新设备"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法添加设备")

    # 检查设备ID是否已存在
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="设备ID已存在")

    db_device = Device(
        name=device.name,
        device_type=device.device_type,
        device_id=device.device_id,
        room_id=device.room_id,
        house_id=current_user.house_id,
        status={"power": False}  # 默认状态
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)

    return db_device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
        device_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取单个设备信息"""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.house_id == current_user.house_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")

    # 访客权限检查
    if current_user.role == UserRole.GUEST and device.device_type != "light":
        raise HTTPException(status_code=403, detail="访客只能查看灯光设备")

    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
        device_id: int,
        device_update: DeviceUpdate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """更新设备信息"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法修改设备")

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.house_id == current_user.house_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")

    # 更新设备信息
    if device_update.name is not None:
        device.name = device_update.name
    if device_update.room_id is not None:
        device.room_id = device_update.room_id
    if device_update.is_online is not None:
        device.is_online = device_update.is_online

    db.commit()
    db.refresh(device)

    return device


# 在现有的control_device函数后添加这个新版本，或替换原版本

@router.post("/{device_id}/control")
async def control_device(
        device_id: int,
        control: DeviceControl,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """控制设备（集成MQTT）"""
    device = db.query(Device).filter(
        Device.id == device_id,
        Device.house_id == current_user.house_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")

    if current_user.role == UserRole.GUEST and device.device_type != "light":
        raise HTTPException(status_code=403, detail="访客只能控制灯光设备")

    # 更新数据库状态
    device.status = control.status
    device.is_online = True
    db.commit()

    # 发送MQTT控制指令
    from app.services.mqtt_service import mqtt_service
    mqtt_success = mqtt_service.publish_device_control(device.device_id, {
        "action": control.action,
        "parameters": control.status
    })

    return {
        "message": "设备控制成功",
        "device_id": device_id,
        "device_name": device.name,
        "action": control.action,
        "status": control.status,
        "mqtt_sent": mqtt_success,
        "mqtt_connected": mqtt_service.connected
    }


@router.delete("/{device_id}")
async def delete_device(
        device_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """删除设备"""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="只有房主可以删除设备")

    device = db.query(Device).filter(
        Device.id == device_id,
        Device.house_id == current_user.house_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")

    device_name = device.name
    db.delete(device)
    db.commit()

    return {"message": f"设备 {device_name} 已删除"}


# 房间管理相关接口
@router.get("/rooms/", response_model=List[RoomResponse])
async def get_rooms(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取房间列表"""
    # 查询房间及其设备数量
    rooms_query = db.query(
        Room.id,
        Room.name,
        Room.house_id,
        func.count(Device.id).label('device_count')
    ).outerjoin(Device, Room.id == Device.room_id) \
        .filter(Room.house_id == current_user.house_id) \
        .group_by(Room.id, Room.name, Room.house_id) \
        .all()

    rooms = []
    for room_data in rooms_query:
        rooms.append({
            "id": room_data.id,
            "name": room_data.name,
            "house_id": room_data.house_id,
            "device_count": room_data.device_count
        })

    return rooms


@router.post("/rooms/", response_model=RoomResponse)
async def create_room(
        room: RoomCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """创建房间"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法创建房间")

    # 检查房间名是否已存在
    existing_room = db.query(Room).filter(
        Room.name == room.name,
        Room.house_id == current_user.house_id
    ).first()

    if existing_room:
        raise HTTPException(status_code=400, detail="房间名已存在")

    db_room = Room(
        name=room.name,
        house_id=current_user.house_id
    )
    db.add(db_room)
    db.commit()
    db.refresh(db_room)

    return {
        "id": db_room.id,
        "name": db_room.name,
        "house_id": db_room.house_id,
        "device_count": 0
    }