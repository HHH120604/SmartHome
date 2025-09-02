from sqlalchemy.orm import Session
from app.models.scene import Scene, Automation
from app.models.device import Device
from app.models.user import User
import asyncio
from datetime import datetime


class SceneService:
    def __init__(self, db: Session):
        self.db = db

    async def execute_scene(self, scene: Scene, user: User):
        """执行场景"""
        executed_actions = []
        failed_actions = []

        for action_data in scene.actions:
            try:
                device_id = action_data.get("device_id")
                action = action_data.get("action")
                parameters = action_data.get("parameters", {})

                # 获取设备
                device = self.db.query(Device).filter(Device.id == device_id).first()
                if not device:
                    failed_actions.append({
                        "device_id": device_id,
                        "error": "设备不存在"
                    })
                    continue

                # 更新设备状态
                device.status = parameters
                device.is_online = True
                self.db.commit()

                print(f"🎭 场景执行: {device.name} -> {action} -> {parameters}")

                executed_actions.append({
                    "device_id": device_id,
                    "device_name": device.name,
                    "action": action,
                    "parameters": parameters,
                    "timestamp": datetime.now().isoformat()
                })

                # 模拟设备响应时间
                await asyncio.sleep(0.1)

            except Exception as e:
                failed_actions.append({
                    "device_id": action_data.get("device_id"),
                    "error": str(e)
                })

        return {
            "executed_actions": executed_actions,
            "failed_actions": failed_actions,
            "total_actions": len(scene.actions),
            "success_count": len(executed_actions),
            "failed_count": len(failed_actions)
        }

    async def check_automation_conditions(self, automation: Automation):
        """检查自动化条件是否满足"""
        if not automation.is_active:
            return False

        results = []

        for condition_data in automation.conditions:
            condition_type = condition_data.get("type")

            if condition_type == "time":
                # 时间条件检查
                result = self.check_time_condition(condition_data)
            elif condition_type == "sensor":
                # 传感器条件检查
                result = await self.check_sensor_condition(condition_data)
            elif condition_type == "device":
                # 设备状态条件检查
                result = self.check_device_condition(condition_data)
            else:
                result = False

            results.append(result)

        # 根据条件逻辑判断
        if automation.condition_logic == "AND":
            return all(results)
        else:  # OR
            return any(results)

    def check_time_condition(self, condition):
        """检查时间条件"""
        # 实现时间条件逻辑
        # 例如：{"type": "time", "parameter": "hour", "operator": "==", "value": "18"}
        try:
            now = datetime.now()
            parameter = condition.get("parameter")
            operator = condition.get("operator")
            value = int(condition.get("value"))

            if parameter == "hour":
                current_value = now.hour
            elif parameter == "minute":
                current_value = now.minute
            else:
                return False

            if operator == "==":
                return current_value == value
            elif operator == ">":
                return current_value > value
            elif operator == "<":
                return current_value < value

        except:
            return False

        return False

    async def check_sensor_condition(self, condition):
        """检查传感器条件"""
        # 实现传感器数据条件检查
        # 例如：{"type": "sensor", "device_id": "sensor_001", "parameter": "temperature", "operator": ">", "value": "25"}
        try:
            from app.models.sensor_data import SensorData

            device_id = condition.get("device_id")
            parameter = condition.get("parameter")
            operator = condition.get("operator")
            value = float(condition.get("value"))

            # 获取最新传感器数据
            latest_data = self.db.query(SensorData).filter(
                SensorData.device_id == device_id
            ).order_by(SensorData.timestamp.desc()).first()

            if not latest_data:
                return False

            # 获取传感器值
            if parameter == "temperature":
                current_value = latest_data.temperature
            elif parameter == "humidity":
                current_value = latest_data.humidity
            elif parameter == "gas_level":
                current_value = latest_data.gas_level
            else:
                return False

            if current_value is None:
                return False

            # 比较值
            if operator == "==":
                return abs(current_value - value) < 0.1
            elif operator == ">":
                return current_value > value
            elif operator == "<":
                return current_value < value
            elif operator == ">=":
                return current_value >= value
            elif operator == "<=":
                return current_value <= value

        except:
            return False

        return False

    def check_device_condition(self, condition):
        """检查设备状态条件"""
        # 实现设备状态条件检查
        try:
            device_id = condition.get("device_id")
            parameter = condition.get("parameter")
            operator = condition.get("operator")
            value = condition.get("value")

            device = self.db.query(Device).filter(Device.device_id == device_id).first()
            if not device or not device.status:
                return False

            current_value = device.status.get(parameter)
            if current_value is None:
                return False

            # 类型转换和比较
            if operator == "==":
                return str(current_value) == str(value)
            elif operator != "==":
                try:
                    current_value = float(current_value)
                    value = float(value)
                    if operator == ">":
                        return current_value > value
                    elif operator == "<":
                        return current_value < value
                    elif operator == ">=":
                        return current_value >= value
                    elif operator == "<=":
                        return current_value <= value
                except:
                    return False

        except:
            return False

        return False