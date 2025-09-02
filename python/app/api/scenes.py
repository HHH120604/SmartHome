from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import time

from app.database import get_db
from app.models.scene import Scene, SceneExecutionLog, Automation
from app.models.device import Device
from app.models.user import User, UserRole
from app.schemas.scene import (
    SceneCreate, SceneResponse, SceneUpdate,
    SceneExecutionResult, AutomationCreate, AutomationResponse
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[SceneResponse])
async def get_scenes(
        category: Optional[str] = Query(None, description="场景分类筛选"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取场景列表"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法访问场景功能")

    scenes = db.query(Scene).filter(Scene.house_id == current_user.house_id).all()

    # 为每个场景计算涉及的设备数量
    result = []
    for scene in scenes:
        device_count = len(scene.actions) if scene.actions else 0
        scene_dict = {
            "id": scene.id,
            "name": scene.name,
            "description": scene.description,
            "actions": scene.actions,
            "icon": scene.icon,
            "color": scene.color,
            "created_by": scene.created_by,
            "created_at": scene.created_at,
            "device_count": device_count
        }
        result.append(SceneResponse(**scene_dict))

    return result


@router.post("/", response_model=SceneResponse)
async def create_scene(
        scene: SceneCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """创建场景"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法创建场景")

    # 检查场景名称是否重复
    existing_scene = db.query(Scene).filter(
        Scene.name == scene.name,
        Scene.house_id == current_user.house_id
    ).first()
    if existing_scene:
        raise HTTPException(status_code=400, detail="场景名称已存在")

    # 验证所有设备是否存在且有权限
    device_ids = [action.device_id for action in scene.actions]
    devices = db.query(Device).filter(
        Device.id.in_(device_ids),
        Device.house_id == current_user.house_id
    ).all()

    if len(devices) != len(device_ids):
        found_ids = [d.id for d in devices]
        missing_ids = [d for d in device_ids if d not in found_ids]
        raise HTTPException(
            status_code=400,
            detail=f"以下设备不存在或无权限: {missing_ids}"
        )

    # 创建场景
    db_scene = Scene(
        name=scene.name,
        description=scene.description,
        house_id=current_user.house_id,
        actions=[action.dict() for action in scene.actions],
        icon=scene.icon,
        color=scene.color,
        created_by=current_user.id
    )
    db.add(db_scene)
    db.commit()
    db.refresh(db_scene)

    return SceneResponse(
        id=db_scene.id,
        name=db_scene.name,
        description=db_scene.description,
        actions=db_scene.actions,
        icon=db_scene.icon,
        color=db_scene.color,
        created_by=db_scene.created_by,
        created_at=db_scene.created_at,
        device_count=len(scene.actions)
    )


# 在execute_scene函数中，找到执行场景的部分，更新为：

@router.post("/{scene_id}/execute", response_model=SceneExecutionResult)
async def execute_scene(
        scene_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """执行场景（集成MQTT）"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法执行场景")

    scene = db.query(Scene).filter(
        Scene.id == scene_id,
        Scene.house_id == current_user.house_id
    ).first()

    if not scene:
        raise HTTPException(status_code=404, detail="场景未找到")

    print(f"Executing scene: {scene.name}")
    start_time = time.time()

    # 发送场景执行MQTT消息
    from app.services.mqtt_service import mqtt_service
    mqtt_success = mqtt_service.publish_scene_execution(scene.name, scene.actions)

    # 执行场景动作
    executed_actions = []
    failed_actions = []

    for action_data in scene.actions:
        try:
            device_id = action_data.get("device_id")
            action = action_data.get("action")
            parameters = action_data.get("parameters", {})

            device = db.query(Device).filter(Device.id == device_id).first()
            if not device:
                failed_actions.append({
                    "device_id": device_id,
                    "error": "设备不存在",
                    "action": action
                })
                continue

            # 更新数据库状态
            old_status = device.status.copy() if device.status else {}
            device.status = parameters
            device.is_online = True
            db.commit()

            # 发送MQTT控制指令
            mqtt_device_success = mqtt_service.publish_device_control(device.device_id, {
                "action": action,
                "parameters": parameters
            })

            print(f"Device: {device.name} -> {action}, MQTT: {mqtt_device_success}")

            executed_actions.append({
                "device_id": device_id,
                "device_name": device.name,
                "device_type": device.device_type,
                "action": action,
                "old_status": old_status,
                "new_status": parameters,
                "mqtt_sent": mqtt_device_success,
                "timestamp": datetime.now().isoformat()
            })

            await asyncio.sleep(0.2)

        except Exception as e:
            failed_actions.append({
                "device_id": action_data.get("device_id"),
                "action": action_data.get("action"),
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    execution_time = time.time() - start_time
    success = len(failed_actions) == 0

    print(f"Scene completed: {scene.name}, Success: {success}, Time: {execution_time:.2f}s")

    # 记录执行日志
    execution_log = SceneExecutionLog(
        scene_id=scene_id,
        executed_by=current_user.id,
        house_id=current_user.house_id,
        execution_result={
            "executed_actions": executed_actions,
            "failed_actions": failed_actions,
            "execution_time": execution_time,
            "mqtt_scene_sent": mqtt_success
        },
        success=success,
        error_message=None if success else f"{len(failed_actions)} actions failed"
    )
    db.add(execution_log)
    db.commit()

    return SceneExecutionResult(
        scene_id=scene_id,
        scene_name=scene.name,
        success=success,
        executed_actions=executed_actions,
        failed_actions=failed_actions,
        execution_time=round(execution_time, 2),
        total_devices=len(scene.actions),
        success_count=len(executed_actions),
        failed_count=len(failed_actions)
    )


# 自动化规则相关接口
@router.get("/automations/", response_model=List[AutomationResponse])
async def get_automations(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取自动化规则列表"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法访问自动化功能")

    automations = db.query(Automation).filter(
        Automation.house_id == current_user.house_id
    ).all()
    return automations


@router.post("/automations/", response_model=AutomationResponse)
async def create_automation(
        automation: AutomationCreate,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """创建自动化规则"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法创建自动化")

    # 验证动作中的设备权限
    for action in automation.actions:
        device = db.query(Device).filter(
            Device.id == action.device_id,
            Device.house_id == current_user.house_id
        ).first()
        if not device:
            raise HTTPException(
                status_code=400,
                detail=f"设备 {action.device_id} 不存在或无权限"
            )

    db_automation = Automation(
        name=automation.name,
        house_id=current_user.house_id,
        conditions=[condition.dict() for condition in automation.conditions],
        actions=[action.dict() for action in automation.actions],
        condition_logic=automation.condition_logic,
        created_by=current_user.id
    )
    db.add(db_automation)
    db.commit()
    db.refresh(db_automation)

    return db_automation

# 其他基础CRUD接口省略，您可以根据需要添加