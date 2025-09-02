import paho.mqtt.client as mqtt
import json
from typing import Dict, List, Optional
import threading


class MQTTService:
    def __init__(self):
        # MQTT客户端初始化
        self.client = mqtt.Client(client_id="smart_home")
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
            print("INFO:\t✅ MQTT connected")
        else:
            self.connected = False
            print(f"WARN:\t❌ MQTT connection failed, code: {rc}")
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
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))

            print(f"MQTT message: {topic}")
            print(payload)

        except Exception as e:
            print(f"MQTT message error: {e}")

    def subscribe_topics(self):
        """订阅MQTT主题"""
        topics = [
            ("hi3861/publish", 1), # 传感器发送数据
        ]

        for topic, qos in topics:
            result = self.client.subscribe(topic, qos)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                print(f"Subscribed: {topic}")

    def publish_device_control(self, message: dict) -> bool:
        """发布设备控制指令"""
        # if not self.connected:
        #     print("MQTT not connected")
        #     return False

        topic = "hi3861/subscribe" # 传感器接收的主题
        # try:
        MODULES = [
            "FIRE_MODULE",
            "GAS_MODULE",
            "LCD_MODULE",
            "LED_MODULE",
            "MQTT_MODULE",
            "PIR_MODULE",
            "TAH_MODULE"
        ]
        control_code = ""

        for module in MODULES:
            value = message.get(module, 0)  # 没有就默认0
            control_code += str(value)
        print(control_code)
        #     result = self.client.publish(topic, json.dumps(message, ensure_ascii=False))
        #     if result.rc == mqtt.MQTT_ERR_SUCCESS:
        #         print(f"Control sent: {message}")
        #         return True
        #     else:
        #         print(f"Control send failed: {result.rc}")
        #         return False
        # except Exception as e:
        #     print(f"Control send error: {e}")
        return False

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
            host = "localhost"
            port = 1883
            user = "hi3861_python"
            password = "a123456789"
            print(f"INFO:\t✅ Starting MQTT service: {host}:{port}")

            # 设置认证信息
            if user and password:
                self.client.username_pw_set(user, password)

            # 连接MQTT broker
            self.client.connect(host, port, 60)
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
message = {
    "LCD_MODULE": 1,
    "LED_MODULE": 1,
    "MQTT_MODULE": 1,
}
mqtt_service.publish_device_control(message)