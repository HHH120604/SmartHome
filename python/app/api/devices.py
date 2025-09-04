import random
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


@router.get("/{username}", response_model=dict[str, dict[int, DeviceResponse]])
async def get_devices(
    username: str,
    # room_id: int = None,
    # device_type: str = None,
    # current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取设备列表"""
    query = db.query(Device, User.username, Room.name) \
        .join(User, Device.user_id == User.id) \
        .join(Room, Device.room_id == Room.id) \
        .filter(User.username == username, Device.house_id == 1)

    # 访客只能看到灯光设备
    # if current_user.role == UserRole.GUEST:
    #     query = query.filter(Device.device_type == "light")

    # 筛选条件
    # if room_id:
    #     query = query.filter(Device.room_id == room_id)
    # if device_type:
    #     query = query.filter(Device.device_type == device_type)
    devices = {
        username : {
            device[0].id : {
                "id": device[0].id,
                "type": device[0].device_type,
                "name": device[0].name,
                "on": device[0].status["power"],
                "status": device[0].status,
                "scene": device[2],
                "online": device[0].is_online,
                "desc": device[0].description,
            } for device in query.all()
        }
    }
    
    return devices


@router.post("/{username}", response_model=DeviceResponse)
async def create_device(
        username: str,
        device_in: DeviceCreate,
        db: Session = Depends(get_db)
):
    """添加新设备"""
    query = db.query(User).filter(User.username == username).first()
    if not query:
        raise HTTPException(status_code=400, detail="用户ID不存在")
    
    if (device_in.device_type == "air"):
        status = {"power": False, "mode": "cool", "temp": 26}
    elif (device_in.device_type == "shower"):
        status = {"power": False, "temp": 40}
    elif (device_in.device_type == "fan"):
        status = {"power": False, "level": 0}
    else:
        status = {"power": False}
    device = Device(
        name=device_in.name,
        device_type=device_in.device_type,
        device_id=f"{device_in.device_type}_{random.randint(1, 99999):05d}",
        user_id=query.id,
        room_id=device_in.room_id,
        house_id=1,
        status=status,  # 默认状态
        is_online=True,
        description="已关闭",
    )

    # 检查设备ID是否已存在
    existing_device = db.query(Device).filter(Device.device_id == device.device_id).first()
    if existing_device:
        raise HTTPException(status_code=400, detail="设备ID已存在")

    db.add(device)
    db.commit()
    db.refresh(device)
    
    query = db.query(Room).filter(Room.id == device_in.room_id).first()
    device_out = {
        "id": device.id,
        "type": device.device_type,
        "name": device.name,
        "on": device.status["power"],
        "status": device.status,
        "scene": query.name,
        "online": device.is_online,
        "desc": device.description,
    }

    return device_out


# @router.get("/{user_id}/{device_id}", response_model=DeviceResponse)
# async def get_device(
#         device_id: int,
#         current_user: User = Depends(get_current_user),
#         db: Session = Depends(get_db)
# ):
#     """获取单个设备信息"""
#     device = db.query(Device).filter(
#         Device.id == device_id,
#         Device.house_id == current_user.house_id
#     ).first()

#     if not device:
#         raise HTTPException(status_code=404, detail="设备未找到")

#     # 访客权限检查
#     if current_user.role == UserRole.GUEST and device.device_type != "light":
#         raise HTTPException(status_code=403, detail="访客只能查看灯光设备")

#     return device


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

@router.post("/control/{username}")
async def control_device(
        username: str,
        control: list[DeviceControl],
        db: Session = Depends(get_db)
):
    """控制设备（集成MQTT）"""
    module_control = [0,0,0,1,0,1,0,0]
    device_control = [2,0,0,0,0,0,0,0,0,0]
    for cmd in control:
        device = db.query(Device).join(User, User.id == Device.user_id \
        ).filter(
            User.username == username,
            Device.id == cmd.device_id,
        ).first()
        print(device.name)
        if not device:
            raise HTTPException(status_code=404, detail="设备未找到")
        # 更新数据库状态
        device.status = cmd.status
        device.is_online = True
        if device.status["power"]:
            if device.device_type == "air":
                module_control[device.module] = 1
                device_control[device.device] = 1
            else:
                module_control[device.module] = 1
                device_control[device.device] = 1
        else:
            module_control[device.module] = 0
            device_control[device.device] = 0
        db.commit()
    module_control[0] = 0
    device_control[0] = 2

    # 发送MQTT控制指令
    from app.services.mqtt_service import mqtt_service
    mqtt_service.publish_device_control(''.join(map(str, module_control)), ''.join(map(str, device_control)))

    return {}


@router.delete("/{username}/{device_id}")
async def delete_device(
        username: str,
        device_id: int,
        db: Session = Depends(get_db)
):
    """删除设备"""
    user = db.query(User).filter(User.username == username).first()
    device = db.query(Device).filter(
        Device.id == device_id,
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")
    
    if device.user_id != user.id:
        raise HTTPException(status_code=404, detail="该用户没有此设备的控制权限")

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