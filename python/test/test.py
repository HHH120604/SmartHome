import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
import random
import logging

# 启用日志输出
logging.basicConfig(level=logging.DEBUG)

# MQTT服务器地址和端口
broker = 'broker.emqx.io'
port = 1883
topic = "/python/mqtt"
client_id = f'python-mqtt-{random.randint(0, 1000)}'

# 连接成功回调函数
def on_connect(client, userdata, connect_flags, rc, properties):
    if rc == 0:
        print("连接到MQTT代理成功")
        client.subscribe(topic)  # 订阅主题
    else:
        print(f"连接失败，返回码 {rc}")

# 消息接收回调函数
def on_message(client, userdata, msg):
    print(f"收到消息：主题={msg.topic}，内容={msg.payload.decode()}")

# 创建MQTT客户端实例
client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2, client_id=client_id)
client.on_connect = on_connect
client.on_message = on_message

# 连接到MQTT代理
client.connect(broker, port)

# 启动网络循环
client.loop_start()

# 保持运行，直到用户中断
try:
    while True:
        pass
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
    print("客户端已断开连接")