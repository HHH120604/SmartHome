from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# current_dir = os.path.dirname(os.path.abspath(__file__))
# project_root = os.path.dirname(current_dir)
# if project_root not in sys.path:
#     sys.path.insert(0, project_root)

from app.api import auth, devices, sensors, scenes, mqtt_devices, ai_chat
from app.config import settings
from app.database import init_db
from app.services.mqtt_service import mqtt_service
from app.services.ai_service import ai_service

# 应用启动和关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动事件"""
    # 初始化数据库
    init_db()
    print("🚀 Starting Hongmeng Smart Home API")
    print("📡 Starting MQTT service...")
    mqtt_service.start()
    print("🤖 AI Assistant service initialized")
    print(f"📚 API docs: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔗 WebSocket endpoint: ws://{settings.HOST}:{settings.PORT}/ws/chat")
    print("=" * 60)
    print("🎯 AI功能特色：")
    print("  • 模糊意图理解：'灯太亮了' → 自动调暗亮度")
    print("  • 上下文对话：'空调多少度？' '低一点' → 理解并执行")
    print("  • 一键创建场景：'设置电影模式' → 自动配置设备")
    print("  • 数据智能分析：环境异常检测、设备故障诊断")
    print("  • 习惯学习：'每天7点起床' → 自动创建起床场景")
    print("  • 动态调整：根据天气、时间智能建议")
    print("=" * 60)
    yield
    """应用关闭事件"""
    print("🛑 Stopping Hongmeng Smart Home API")
    mqtt_service.stop()
    print("🤖 AI Assistant service stopped")

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["用户认证"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["设备管理"])
app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["传感器数据"])
app.include_router(scenes.router, prefix="/api/v1/scenes", tags=["场景管理"])
app.include_router(mqtt_devices.router, prefix="/api/v1/mqtt", tags=["MQTT设备"])
app.include_router(ai_chat.router, prefix="/api/v1/ai", tags=["AI智能助手"])

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "mqtt_connected": mqtt_service.connected,
        "ai_assistant": "enabled",
        "websocket_endpoint": f"ws://{settings.HOST}:{settings.PORT}/ws/chat",
        "features": [
            "用户认证管理",
            "设备远程控制",
            "传感器数据监控",
            "智能场景管理",
            "MQTT硬件通信",
            "🤖 AI智能助手 (NEW!)",
            "🧠 模糊意图理解",
            "💬 上下文长对话",
            "🎬 一键创建场景",
            "📊 智能数据分析",
            "🎯 习惯学习推荐"
        ]
    }

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "database": "sqlite",
        "mqtt_status": "connected" if mqtt_service.connected else "disconnected",
        "ai_assistant": "active",
        "websocket_available": True,
        "version": settings.VERSION
    }

@app.get("/ai/status")
async def ai_status():
    """AI助手状态检查"""
    return {
        "ai_service": "active",
        "model": "qwen-turbo",
        "features": {
            "intent_understanding": True,
            "context_conversation": True,
            "scene_creation": True,
            "data_analysis": True,
            "habit_learning": True,
            "dynamic_adjustment": True
        },
        "supported_languages": ["中文", "English"],
        "voice_support": True,
        "conversation_memory": True,
        "websocket_support": True
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )