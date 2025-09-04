import os
from dotenv import load_dotenv
load_dotenv()  # 加载项目根目录下的 .env 文件

class Settings:
    # 数据库配置
    DATABASE_URL = os.getenv("DATABASE_URL")

    # 安全配置
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = eval(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

    # MQTT配置
    MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST") # MQTT地址
    MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT"))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

    # 应用配置
    DEBUG = os.getenv("DEBUG")
    HOST = os.getenv("HOST")
    PORT = int(os.getenv("PORT"))

    # 项目信息
    PROJECT_NAME = os.getenv("PROJECT_NAME")
    VERSION = os.getenv("VERSION")
    DESCRIPTION = os.getenv("DESCRIPTION")

    # AI服务配置
    AI_MODEL = "qwen-plus"
    AI_TIMEOUT = 30
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

    # WebSocket配置
    WEBSOCKET_HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）
    MAX_WEBSOCKET_CONNECTIONS = 100  # 最大连接数

settings = Settings()