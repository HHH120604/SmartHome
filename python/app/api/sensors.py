from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app.models.sensor_data import SensorData, AlertLog
from app.models.user import User, UserRole
from app.schemas.sensor import (
    SensorDataResponse, EnvironmentSummary,
    SensorDataCreate, AlertResponse, AlertCreate
)
from app.api.auth import get_current_user

router = APIRouter()


@router.get("/latest/{type}/{range}", response_model=list[float])
async def get_latest_sensor_data(
    type: str,
    range: str,
    db: Session = Depends(get_db)
):
    """获取最新环境数据摘要"""
    time_format = {
        "3hours": '%Y-%m-%d %H:%M:00',
        "day": '%Y-%m-%d %H:00:00',
        "15days": '%Y-%m-%d'
    }
    num_data = {
        "3hours": 18,
        "day": 24,
        "15days": 15
    }

    if type == "temperature":
        query = db.query(
            func.strftime(time_format[range], SensorData.timestamp).label('time'),
            func.avg(SensorData.temperature).label('avg')
        ).filter(
            SensorData.temperature != None, SensorData.timestamp >= (datetime.now() - timedelta(hours=3))
        ).group_by(
            func.strftime(time_format[range], SensorData.timestamp)
        ).order_by(
            desc('time')
        )
    elif type == "humidity":
        query = db.query(
            func.strftime(time_format[range], SensorData.timestamp).label('time'),
            func.avg(SensorData.humidity).label('avg')
        ).filter(
            SensorData.humidity != None, SensorData.timestamp >= (datetime.now() - timedelta(hours=3))
        ).group_by(
            func.strftime(time_format[range], SensorData.timestamp)
        ).order_by(
            desc('time')
        )
    data = [data.avg for data in query.all()]
    if not data:
        data = [0]
    while (len(data) < num_data[range]):
        data.append(data[-1])
    if range == "3hours" and len(data) > num_data[range]:
        data = data[::10]
    data = [round(data, 2) for data in data]
    return data


@router.get("/latest", response_model=SensorDataResponse)
async def get_sensor_history(
        db: Session = Depends(get_db)
):
    """获取历史传感器数据"""
    data = {
        "temp": db.query(SensorData.temperature).filter(SensorData.temperature > 0).order_by(desc(SensorData.timestamp)).limit(1).first(),
        "humidity": db.query(SensorData.humidity).filter(SensorData.humidity != None).order_by(desc(SensorData.timestamp)).limit(1).first(),
        "gasConcentration": db.query(SensorData.gas_level).filter(SensorData.gas_level > 0).order_by(desc(SensorData.timestamp)).limit(1).first(),
        "flameLevel": db.query(SensorData.flame_detected).filter(SensorData.flame_detected != None).order_by(desc(SensorData.timestamp)).limit(1).first(),
    }
    for k, v in data.items():
        if v:
            data[k] = round(v[0], 2)
        else:
            data[k] = 0
    data["tempStatus"] = "normal"
    data["humidityStatus"] = "normal"
    data["timestamp"] = datetime.now()
    return data


@router.post("/data")
async def receive_sensor_data(
        data: SensorDataCreate,
        db: Session = Depends(get_db)
):
    """接收硬件传感器数据（由MQTT服务或硬件直接调用）"""
    sensor_data = SensorData(
        device_id=data.device_id,
        house_id=1,  # 默认房屋ID，实际项目中应该从设备信息获取
        temperature=data.temperature,
        humidity=data.humidity,
        light_intensity=data.light_intensity,
        gas_level=data.gas_level,
        flame_detected=data.flame_detected,
        soil_moisture=data.soil_moisture,
        data_json=data.data_json
    )

    db.add(sensor_data)
    db.commit()
    db.refresh(sensor_data)

    # 检查是否需要触发警报
    alerts = await check_and_create_alerts(sensor_data, db)

    response = {"message": "数据接收成功", "sensor_data_id": sensor_data.id}
    if alerts:
        response["alerts"] = alerts

    return response


async def check_and_create_alerts(sensor_data: SensorData, db: Session):
    """检查传感器数据并创建警报"""
    alerts = []

    # 火焰检测
    if sensor_data.flame_detected:
        alert = AlertLog(
            house_id=sensor_data.house_id,
            device_id=sensor_data.device_id,
            alert_type="fire",
            message="检测到火焰，请立即查看！",
            severity="high"
        )
        db.add(alert)
        alerts.append("🔥 检测到火焰")

    # 可燃气体检测
    if sensor_data.gas_level and sensor_data.gas_level > 80:
        alert = AlertLog(
            house_id=sensor_data.house_id,
            device_id=sensor_data.device_id,
            alert_type="gas",
            message=f"可燃气体浓度过高({sensor_data.gas_level}%)，请注意安全！",
            severity="high"
        )
        db.add(alert)
        alerts.append(f"⚠️ 可燃气体浓度: {sensor_data.gas_level}%")

    # 温度异常
    if sensor_data.temperature and sensor_data.temperature > 35:
        alert = AlertLog(
            house_id=sensor_data.house_id,
            device_id=sensor_data.device_id,
            alert_type="temperature",
            message=f"室内温度过高({sensor_data.temperature}°C)，建议开启空调",
            severity="medium"
        )
        db.add(alert)
        alerts.append(f"🌡️ 高温警报: {sensor_data.temperature}°C")

    # 土壤湿度过低（植物养护）
    if sensor_data.soil_moisture and sensor_data.soil_moisture < 20:
        alert = AlertLog(
            house_id=sensor_data.house_id,
            device_id=sensor_data.device_id,
            alert_type="soil",
            message=f"土壤湿度过低({sensor_data.soil_moisture}%)，需要浇水",
            severity="low"
        )
        db.add(alert)
        alerts.append(f"🌱 需要浇水: {sensor_data.soil_moisture}%")

    if alerts:
        db.commit()
        print(f"⚠️ 生成 {len(alerts)} 个警报")

    return alerts


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
        resolved: bool = Query(None, description="是否已解决"),
        limit: int = Query(50, description="返回数量限制", le=200),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取警报列表"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看警报")

    query = db.query(AlertLog).filter(AlertLog.house_id == current_user.house_id)

    if resolved is not None:
        query = query.filter(AlertLog.is_resolved == resolved)

    alerts = query.order_by(desc(AlertLog.created_at)).limit(limit).all()

    return alerts


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(
        alert_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """标记警报为已解决"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法处理警报")

    alert = db.query(AlertLog).filter(
        AlertLog.id == alert_id,
        AlertLog.house_id == current_user.house_id
    ).first()

    if not alert:
        raise HTTPException(status_code=404, detail="警报未找到")

    alert.is_resolved = True
    alert.resolved_at = datetime.now()
    db.commit()

    return {"message": "警报已标记为解决", "alert_id": alert_id}