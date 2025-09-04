import paho.mqtt.client as mqtt
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import threading
import time

from app.config import settings
from app.database import SessionLocal
from app.models.device import Device
from app.models.sensor_data import SensorData, AlertLog


class MQTTService:
    def __init__(self):
        # MQTT客户端初始化
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        # 连接状态管理
        self.connected = False
        self.connection_retry_count = 0
        self.max_retry = 5

        # 设备状态缓存
        self.device_status_cache: Dict[str, dict] = {}
        self.online_devices: List[str] = []
        self.running = False

    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            self.connection_retry_count = 0
            self.subscribe_topics()
            print("MQTT connected")
        else:
            self.connected = False
            print(f"MQTT connection failed, code: {rc}")
            self.handle_connection_error(rc)

    def on_disconnect(self, client, userdata, rc):
        """MQTT断开连接回调"""
        self.connected = False
        self.online_devices.clear()
        print(f"MQTT disconnected, code: {rc}")
        if rc != 0:
            self.reconnect()

    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        try:
            payload = msg.payload.decode('utf-8')
            hi_data = payload.split(',')
            data = SensorData(
                device_id="hi3861_001",
                temperature = float(hi_data[4]),  # 温度
                humidity = float(hi_data[5]),  # 湿度
                human_detected = int(hi_data[2]),  # 人体检测
                light_intensity = int(hi_data[3]),  # 光照强度
                gas_level = float(hi_data[1]),  # 可燃气体浓度
                flame_detected = int(hi_data[0]),  # 是否检测到火焰
                timestamp = datetime.now(),
            )
            self.check_and_send_alerts(data)

            db = SessionLocal()
            db.add(data)
            db.commit()
            db.close()

        except Exception as e:
            print(f"MQTT message error: {e}")

    def subscribe_topics(self):
        """订阅MQTT主题"""
        topics = [
            # ("hongmeng/sensors/+/data", 1),  # 传感器数据
            # ("hongmeng/devices/+/status", 1),  # 设备状态
            # ("hongmeng/devices/+/heartbeat", 0),  # 设备心跳
            # ("hongmeng/system/alerts", 1),  # 系统警报
            ("hi3861/publish", 1),
        ]

        for topic, qos in topics:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                print(f"Subscribed: {topic}")

    async def handle_sensor_data(self, data: dict):
        """处理传感器数据"""
        try:
            device_id = data.get("device_id")
            if not device_id:
                return

            # 保存到数据库
            db = SessionLocal()
            sensor_data = SensorData(
                device_id=device_id,
                house_id=data.get("house_id", 1),
                temperature=data.get("temperature"),
                humidity=data.get("humidity"),
                light_intensity=data.get("light_intensity"),
                gas_level=data.get("gas_level"),
                flame_detected=data.get("flame_detected", False),
                soil_moisture=data.get("soil_moisture"),
                data_json=data
            )
            db.add(sensor_data)
            db.commit()

            print(f"Sensor data saved: {device_id}")

            # 检查警报条件
            # await self.check_and_send_alerts(sensor_data, db)
            db.close()

        except Exception as e:
            print(f"Sensor data error: {e}")

    async def handle_device_status(self, data: dict):
        """处理设备状态更新"""
        try:
            device_id = data.get("device_id")
            if not device_id:
                return

            # 更新设备状态缓存
            self.device_status_cache[device_id] = {
                "status": data.get("status", {}),
                "is_online": True,
                "last_update": datetime.now().isoformat(),
                "battery": data.get("battery"),
                "signal_strength": data.get("signal_strength")
            }

            # 更新数据库中的设备状态
            db = SessionLocal()
            device = db.query(Device).filter(Device.device_id == device_id).first()
            if device:
                device.status = data.get("status", {})
                device.is_online = True
                db.commit()
                print(f"Device status updated: {device.name}")

            db.close()

        except Exception as e:
            print(f"Device status error: {e}")

    def handle_device_heartbeat(self, data: dict):
        """处理设备心跳"""
        device_id = data.get("device_id")
        if device_id:
            if device_id not in self.online_devices:
                self.online_devices.append(device_id)
                print(f"Device online: {device_id}")

            # 更新心跳时间
            if device_id in self.device_status_cache:
                self.device_status_cache[device_id]["last_heartbeat"] = datetime.now().isoformat()

    def check_and_send_alerts(self, sensor_data: SensorData):
        """检查传感器数据并发送警报"""
        alerts = []
        db = SessionLocal()
        # 火焰检测
        if sensor_data.flame_detected:
            alerts.append({
                "type": "fire",
                "severity": "high",
                "message": "Fire detected",
                "device_id": sensor_data.device_id
            })

        # 可燃气体检测
        if sensor_data.gas_level and sensor_data.gas_level > 300:
            alerts.append({
                "type": "gas",
                "severity": "high",
                "message": f"可燃气体检测超标: {sensor_data.gas_level}pp",
                "device_id": sensor_data.device_id
            })

        # 温度异常
        if sensor_data.temperature and sensor_data.temperature > 35:
            alerts.append({
                "type": "temp",
                "severity": "medium",
                "message": f"室内温度过高: {sensor_data.temperature}°C",
                "device_id": sensor_data.device_id
            })
            
        # 人体检测
        if sensor_data.human_detected and sensor_data.human_detected > 1000:
            alerts.append({
                "type": "human",
                "severity": "medium",
                "message": f"有人经过，请注意！",
                "device_id": sensor_data.device_id
            })

        # 土壤湿度过低
        # if sensor_data.soil_moisture and sensor_data.soil_moisture < 20:
        #     alerts.append({
        #         "type": "soil",
        #         "severity": "low",
        #         "message": f"Low soil moisture: {sensor_data.soil_moisture}%",
        #         "device_id": sensor_data.device_id
        #     })

        # 处理警报
        for alert in alerts:
            # 保存到数据库
            alert_log = AlertLog(
                device_id=sensor_data.device_id,
                house_id=sensor_data.house_id,
                alert_type=alert["type"],
                message=alert["message"],
                severity=alert["severity"],
                created_at=datetime.now(),
            )
            db.add(alert_log)
            print(f"alert: {alert_log.message}")    

            # 通过MQTT发送警报
            # self.publish_alert(alert)
            # print(f"Alert: {alert['type']} - {alert['message']}")

        if alerts:
            db.commit()

    def publish_device_control(self, module: str, device: str) -> bool:
        """发布设备控制指令"""
        if not self.connected:
            print("MQTT not connected")
            return False

        topic = f"hi3861/subscribe"

        try:
            # result = self.client.publish(topic, device)
            # if result.rc == mqtt.MQTT_ERR_SUCCESS:
            #     print(f"Control device sent: {device}")
            # else:
            #     print(f"Control device send failed: {result.rc}")
            #     return False
            # time.sleep(1)
            result = self.client.publish(topic, module)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Control module sent: {module}")
            else:
                print(f"Control module send failed: {result.rc}")
                return False
            time.sleep(1)
            result = self.client.publish(topic, device)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Control device sent: {device}")
            else:
                print(f"Control device send failed: {result.rc}")
                return False
        except Exception as e:
            print(f"Control send error: {e}")
            return False

    def publish_scene_execution(self, scene_name: str, actions: list) -> bool:
        """发布场景执行指令"""
        if not self.connected:
            return False

        topic = "hongmeng/scenes/execute"
        message = {
            "scene_name": scene_name,
            "actions": actions,
            "timestamp": datetime.now().isoformat()
        }

        try:
            result = self.client.publish(topic, json.dumps(message, ensure_ascii=False))
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"Scene executed: {scene_name}")
                return True
            return False
        except Exception as e:
            print(f"Scene execution error: {e}")
            return False

    def publish_alert(self, alert: dict):
        """发布警报消息"""
        if not self.connected:
            return

        topic = f"hongmeng/alerts/{alert.get('device_id', 'system')}"
        message = {
            **alert,
            "timestamp": datetime.now().isoformat()
        }

        try:
            self.client.publish(topic, json.dumps(message, ensure_ascii=False))
        except Exception as e:
            print(f"Alert publish error: {e}")

    def get_device_status(self, device_id: str) -> Optional[dict]:
        """获取设备状态"""
        return self.device_status_cache.get(device_id)

    def get_online_devices(self) -> List[str]:
        """获取在线设备列表"""
        return self.online_devices.copy()

    def handle_connection_error(self, rc: int):
        """处理连接错误"""
        error_messages = {
            1: "Protocol version error",
            2: "Invalid client ID",
            3: "Server unavailable",
            4: "Bad username/password",
            5: "Not authorized"
        }
        error_msg = error_messages.get(rc, f"Unknown error ({rc})")
        print(f"Connection error: {error_msg}")

    def reconnect(self):
        """重连逻辑"""
        if self.connection_retry_count < self.max_retry:
            self.connection_retry_count += 1
            retry_delay = min(2 ** self.connection_retry_count, 60)
            print(f"Reconnecting in {retry_delay}s (attempt {self.connection_retry_count})")
            threading.Timer(retry_delay, self.start).start()
        else:
            print("Max reconnection attempts reached")

    def start(self):
        """启动MQTT服务"""
        if self.running:
            return

        self.running = True
        try:
            print(f"Starting MQTT service: {settings.MQTT_BROKER_HOST}:{settings.MQTT_BROKER_PORT}")

            # 设置认证信息
            if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
                self.client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)

            # 连接MQTT broker
            self.client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            self.client.loop_start()

        except Exception as e:
            print(f"MQTT start error: {e}")
            self.running = False

    def stop(self):
        """停止MQTT服务"""
        if not self.running:
            return

        self.running = False
        print("Stopping MQTT service")

        self.client.loop_stop()
        self.client.disconnect()

        self.connected = False
        self.online_devices.clear()
        self.device_status_cache.clear()


# 全局MQTT服务实例
mqtt_service = MQTTService()