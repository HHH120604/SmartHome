import json
from fastapi import APIRouter, Depends, HTTPException, Body, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import asyncio

# 核心依赖导入
from app.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_user
from app.services.ai_service import ai_service

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API路由
router = APIRouter()


# 添加WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)


manager = ConnectionManager()


# 添加WebSocket路由
@router.websocket("/ws/chat")
async def websocket_chat_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 接收前端发送的消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            user_message = message_data.get("message", "")
            history = message_data.get("history", [])

            if not user_message:
                continue

            # 这里需要获取当前用户，但WebSocket中较难获取JWT token
            # 简化处理：使用默认用户或者通过前端传递token
            try:
                # 获取数据库会话
                db = next(get_db())

                # 简化处理：使用第一个用户（生产环境需要通过token验证）
                current_user = db.query(User).first()
                if not current_user:
                    await websocket.send_text(json.dumps({
                        "error": "未找到用户",
                        "event": "ERROR"
                    }))
                    continue

                # 调用AI服务处理消息
                result = await ai_service.process_message(user_message, current_user, db)
                reply = result.get("reply", "抱歉，我无法理解您的请求。")

                # 模拟流式返回 - 将回复分成小块发送
                tokens = reply.split()
                for i, token in enumerate(tokens):
                    await websocket.send_text(json.dumps({
                        "token": token + " ",
                        "index": i
                    }))
                    await asyncio.sleep(0.05)  # 控制发送速度

                # 发送完成信号
                await websocket.send_text(json.dumps({
                    "event": "DONE",
                    "actions": result.get("actions", []),
                    "suggestions": result.get("suggestions", [])
                }))

                db.close()

            except Exception as e:
                logger.error(f"WebSocket处理消息时出错: {e}")
                await websocket.send_text(json.dumps({
                    "error": f"处理消息时出错: {str(e)}",
                    "event": "ERROR"
                }))

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket客户端断开连接")
    except Exception as e:
        logger.error(f"WebSocket异常: {e}")
        manager.disconnect(websocket)


@router.post("/chat")
async def handle_chat(
        query: str = Body(..., embed=True),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if current_user.role == UserRole.GUEST:
        # 访客只能使用基础对话功能
        allowed_keywords = ['灯', '开', '关', '你好', '状态']
        if not any(keyword in query.lower() for keyword in allowed_keywords):
            raise HTTPException(
                status_code=403,
                detail="访客只能使用基础设备控制和问候功能"
            )

    try:
        # 调用AI服务处理消息
        result = await ai_service.process_message(query, current_user, db)

        return {
            "reply": result.get("reply", "我理解了您的需求"),
            "actions": result.get("actions", []),
            "suggestions": result.get("suggestions", []),
            "intent": result.get("intent", "chat"),
            "timestamp": datetime.now(),
            "user": current_user.username
        }

    except Exception as e:
        logger.error(f"处理AI对话时发生错误: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="处理您的请求时发生内部错误，请稍后重试。"
        )


@router.post("/quick-command")
async def quick_command(
        command: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    快捷指令接口 - 预定义的常用操作
    """
    if current_user.role == UserRole.GUEST:
        # 访客只能使用灯光相关的快捷指令
        allowed_commands = ["全部开灯", "全部关灯"]
        if command not in allowed_commands:
            raise HTTPException(
                status_code=403,
                detail="访客只能使用基础灯光控制指令"
            )

    try:
        # 预定义的快捷指令映射
        quick_commands = {
            "全部开灯": "帮我打开所有房间的灯",
            "全部关灯": "帮我关闭所有房间的灯",
            "回家模式": "执行回家场景，开启客厅灯和空调",
            "睡眠模式": "执行睡眠场景，关闭所有设备",
            "离家模式": "执行离家场景，关闭所有电器",
            "电影模式": "调暗灯光，设置合适的观影环境",
            "检查安全": "检查所有传感器状态和安全情况"
        }

        # 将快捷指令转换为详细指令
        detailed_command = quick_commands.get(command, command)

        # 调用AI服务处理
        result = await ai_service.process_message(detailed_command, current_user, db)

        return {
            "command": command,
            "reply": result.get("reply", "指令已执行"),
            "actions": result.get("actions", []),
            "success": len(result.get("actions", [])) > 0,
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"快捷指令执行失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"快捷指令执行失败: {str(e)}"
        )


@router.get("/daily-summary")
async def get_daily_summary(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取每日数据摘要"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看数据摘要")

    try:
        summary = await ai_service.get_daily_summary(current_user, db)

        return {
            "summary": summary,
            "timestamp": datetime.now(),
            "user": current_user.username
        }

    except Exception as e:
        logger.error(f"生成摘要失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成摘要失败: {str(e)}"
        )


@router.post("/smart-suggestions")
async def get_smart_suggestions(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """获取智能建议"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法获取智能建议")

    try:
        suggestions = ai_service.get_smart_suggestions(current_user, db)

        return {
            "suggestions": suggestions,
            "timestamp": datetime.now(),
            "based_on": "时间、环境数据、设备状态"
        }

    except Exception as e:
        logger.error(f"生成建议失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"生成建议失败: {str(e)}"
        )


@router.get("/conversation-history")
async def get_conversation_history(
        limit: int = 10,
        current_user: User = Depends(get_current_user)
):
    """获取对话历史"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法查看对话历史")

    try:
        history = ai_service.conversation_history

        # 只返回最近的对话记录
        recent_history = history[-limit:] if len(history) > limit else history

        return {
            "conversation_history": recent_history,
            "total_messages": len(history),
            "user": current_user.username,
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"获取对话历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取对话历史失败: {str(e)}"
        )


@router.delete("/conversation-history")
async def clear_conversation_history(
        current_user: User = Depends(get_current_user)
):
    """清空对话历史"""
    if current_user.role == UserRole.GUEST:
        raise HTTPException(status_code=403, detail="访客无法清空对话历史")

    try:
        ai_service.conversation_history = []

        return {
            "message": "对话历史已清空",
            "user": current_user.username,
            "timestamp": datetime.now()
        }

    except Exception as e:
        logger.error(f"清空对话历史失败: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"清空对话历史失败: {str(e)}"
        )


@router.get("/status")
async def get_ai_status():
    """获取AI服务状态"""
    return {
        "ai_service": "active",
        "model": "智能管家模型",
        "features": {
            "intent_understanding": True,
            "context_conversation": True,
            "scene_creation": True,
            "data_analysis": True,
            "habit_learning": True,
            "dynamic_adjustment": True
        },
        "supported_languages": ["中文"],
        "voice_support": False,  # 语音功能可后续添加
        "conversation_memory": True,
        "status": "运行中",
        "timestamp": datetime.now()
    }


# 用于测试的接口
@router.post("/test")
async def test_ai_function(
        test_query: str = Body(..., embed=True),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    AI功能测试接口
    用于测试不同的AI功能模块
    """
    logger.info(f"测试AI功能，查询: {test_query}")

    # 直接调用AI服务进行测试
    result = await ai_service.process_message(test_query, current_user, db)

    return {
        "test_query": test_query,
        "ai_response": result,
        "test_time": datetime.now(),
        "status": "测试完成"
    }