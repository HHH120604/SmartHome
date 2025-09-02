from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user
from app.services.mqtt_service import mqtt_service

router = APIRouter()


@router.get("/online")
async def get_online_devices(current_user: User = Depends(get_current_user)):
    """获取在线设备列表"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看设备状态")

    online_devices = mqtt_service.get_online_devices()
    return {
        "online_count": len(online_devices),
        "devices": online_devices,
        "mqtt_connected": mqtt_service.connected
    }


@router.get("/status/{device_id}")
async def get_device_mqtt_status(
        device_id: str,
        current_user: User = Depends(get_current_user)
):
    """获取设备MQTT状态"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看设备详细状态")

    status = mqtt_service.get_device_status(device_id)
    if not status:
        raise HTTPException(status_code=404, detail="设备未找到或离线")

    return {
        "device_id": device_id,
        "mqtt_status": status
    }


@router.post("/control/{device_id}")
async def control_device_mqtt(
        device_id: str,
        command: Dict[str, Any],
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """通过MQTT控制设备"""
    from app.models.device import Device

    # 验证设备权限
    device = db.query(Device).filter(
        Device.device_id == device_id,
        Device.house_id == current_user.house_id
    ).first()

    if not device:
        raise HTTPException(status_code=404, detail="设备未找到")

    if current_user.role == UserRole.GUEST and device.device_type != "light":
        raise HTTPException(status_code=403, detail="访客只能控制灯光设备")

    # 发送MQTT控制指令
    success = mqtt_service.publish_device_control(device_id, command)

    if success:
        # 更新数据库状态（预期状态）
        device.status = command
        db.commit()

        return {
            "message": "控制指令已发送",
            "device_id": device_id,
            "device_name": device.name,
            "command": command,
            "mqtt_sent": True
        }
    else:
        return {
            "message": "MQTT控制指令发送失败",
            "device_id": device_id,
            "command": command,
            "mqtt_sent": False
        }


@router.get("/service/status")
async def get_mqtt_service_status(current_user: User = Depends(get_current_user)):
    """获取MQTT服务状态"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看服务状态")

    return {
        "mqtt_connected": mqtt_service.connected,
        "service_running": mqtt_service.running,
        "online_devices_count": len(mqtt_service.online_devices),
        "broker_host": mqtt_service.client._host if hasattr(mqtt_service.client, '_host') else "unknown",
        "retry_count": mqtt_service.connection_retry_count
    }


@router.post("/service/restart")
async def restart_mqtt_service(current_user: User = Depends(get_current_user)):
    """重启MQTT服务"""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="只有房主可以重启MQTT服务")

    try:
        mqtt_service.stop()
        mqtt_service.start()
        return {"message": "MQTT服务重启成功"}
    except Exception as e:
        return {"message": f"MQTT服务重启失败: {str(e)}"}