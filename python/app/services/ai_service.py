import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

# 核心依赖导入
from app.models.device import Device, Room
from app.models.scene import Scene
from app.models.sensor_data import SensorData, AlertLog
from app.models.user import User

# Pydantic Schemas
from app.schemas.scene import SceneCreate, SceneAction
from app.schemas.device import DeviceControl

# 提示词管理器
from app.utils.prompts import prompt_manager

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIService:

    def __init__(self):
        # 对话历史记录
        self.conversation_history = []

    async def check_and_alert_safety_issues(self, db: Session, current_user: User) -> str:
        """
        主动检测安全问题并生成警报消息
        返回值：如果有安全问题返回警报消息，否则返回空字符串
        """
        try:
            # 1. 检查数据库中未解决的警报
            active_alerts = db.query(AlertLog).filter(
                AlertLog.house_id == current_user.house_id,
                AlertLog.is_resolved == False
            ).all()

            # 2. 获取最新传感器数据进行实时检测
            latest_kitchen_data = db.query(SensorData).filter(
                SensorData.device_id == "sensor_kitchen_safety",
                SensorData.house_id == current_user.house_id
            ).order_by(SensorData.timestamp.desc()).first()

            # 3. 分析安全威胁
            critical_alerts = []
            high_alerts = []
            medium_alerts = []

            # 3.1 检查数据库中的警报
            for alert in active_alerts:
                if alert.severity == "critical":
                    critical_alerts.append(alert)
                elif alert.severity == "high":
                    high_alerts.append(alert)
                elif alert.severity == "medium":
                    medium_alerts.append(alert)

            # 3.2 实时检测危险数值
            if latest_kitchen_data:
                # 燃气浓度检测
                if latest_kitchen_data.gas_level and latest_kitchen_data.gas_level > 80:
                    critical_alerts.append({
                        "message": f"厨房可燃气体浓度{latest_kitchen_data.gas_level}ppm，严重超标！",
                        "action": "立即关闭燃气阀门，开窗通风，避免使用电器"
                    })
                elif latest_kitchen_data.gas_level and latest_kitchen_data.gas_level > 50:
                    high_alerts.append({
                        "message": f"厨房可燃气体浓度{latest_kitchen_data.gas_level}ppm，超过安全阈值",
                        "action": "请检查燃气设备，增加通风"
                    })

                # 火焰检测
                if latest_kitchen_data.flame_detected:
                    critical_alerts.append({
                        "message": "厨房检测到火焰信号",
                        "action": "请立即确认火源，如有必要拨打119"
                    })

            # 4. 根据威胁级别生成警报消息
            if critical_alerts:
                return self.generate_critical_alert_message(critical_alerts)
            elif high_alerts:
                return self.generate_high_alert_message(high_alerts)
            elif medium_alerts:
                return self.generate_medium_alert_message(medium_alerts)

            # 没有安全问题
            return ""

        except Exception as e:
            logger.error(f"安全检测失败: {e}")
            return ""

    def generate_critical_alert_message(self, alerts: list) -> str:
        """生成严重警报消息"""
        messages = []
        for alert in alerts:
            if isinstance(alert, AlertLog):
                messages.append(f"🔥【紧急警报】{alert.message} 请立即采取行动！")
            else:
                messages.append(f"🔥【紧急警报】{alert['message']} ⚡{alert['action']}")

        return "\n".join(messages) + "\n\n🛡️ 您的安全是我的最高优先级，请立即处理后再进行其他操作！"

    def generate_high_alert_message(self, alerts: list) -> str:
        """生成高级警报消息"""
        messages = []
        for alert in alerts:
            if isinstance(alert, AlertLog):
                messages.append(f"⚠️【安全警报】{alert.message}")
            else:
                messages.append(f"⚠️【安全警报】{alert['message']} 建议：{alert['action']}")

        return "\n".join(messages) + "\n\n请及时处理以上安全问题。"

    def generate_medium_alert_message(self, alerts: list) -> str:
        """生成中级警报消息"""
        messages = []
        for alert in alerts:
            if isinstance(alert, AlertLog):
                messages.append(f"💡【提醒】{alert.message}")
            else:
                messages.append(f"💡【提醒】{alert['message']} {alert['action']}")

        return "\n".join(messages) + "\n\n如需帮助请告诉我。"

    async def process_message(self, query: str, current_user: User, db: Session) -> Dict[str, Any]:
        """
        处理用户消息的主要入口

        Args:
            query: 用户查询
            current_user: 当前用户
            db: 数据库会话

        Returns:
            包含AI回复和操作结果的字典
        """
        try:
            safety_alert = await self.check_and_alert_safety_issues(db, current_user)

            if safety_alert:
                # 如果有安全问题，直接返回安全警报，忽略用户的其他请求
                self.conversation_history.append({"role": "user", "content": query})
                self.conversation_history.append({"role": "assistant", "content": safety_alert})

                return {
                    "reply": safety_alert,
                    "actions": [{"action": "安全警报", "success": True}],
                    "suggestions": ["请立即处理安全问题", "确认安全后再进行其他操作"],
                    "intent": "safety_alert",
                    "priority": "critical"
                }

            # 1. 更新对话历史
            self.conversation_history.append({"role": "user", "content": query})

            # 2. 收集实时上下文数据
            print("收集实时上下文数据")
            context_data = prompt_manager.build_context_data(db, current_user)


            # 3. 构建完整的Prompt
            full_prompt = prompt_manager.build_full_prompt(context_data, self.conversation_history)

            # 4. 调用大模型
            llm_response_json = await self._call_large_language_model(full_prompt, query)

            # 5. 执行LLM返回的动作
            final_response = await self._execute_llm_action(llm_response_json, db, current_user)

            # 6. 更新对话历史
            self.conversation_history.append({"role": "assistant", "content": final_response})

            # 7. 保持对话历史长度
            if len(self.conversation_history) > 20:  # 保留最近20条消息
                self.conversation_history = self.conversation_history[-20:]

            return {
                "reply": final_response,
                "actions": [{"action": "AI处理完成", "success": True}],
                "suggestions": [],
                "intent": llm_response_json.get("action", "unknown")
            }

        except Exception as e:
            logger.error(f"处理AI对话时发生错误: {e}", exc_info=True)
            return {
                "reply": "抱歉，我遇到了一些问题，请稍后再试。",
                "actions": [{"action": "错误处理", "success": False, "message": str(e)}],
                "suggestions": ["请尝试重新描述您的需求"],
                "error": str(e)
            }

    async def _call_large_language_model(self, prompt: str, user_query: str) -> Dict:
        """通义千问API调用 - 最简版本"""
        try:
            import dashscope
            from app.config import settings

            # 设置API密钥
            dashscope.api_key = settings.DASHSCOPE_API_KEY

            # 调用API（使用默认参数）
            from dashscope import Generation

            response = Generation.call(
                model="qwen-turbo",  # 直接写死模型名
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user_query}
                ],
                result_format='message'
            )

            if response.status_code == 200:
                ai_text = response.output.choices[0].message.content

                # 简单的JSON解析
                with open('temp_123.txt', 'a', encoding='utf-8') as f:
                    # json.dump(ai_text, f, ensure_ascii=False, indent=4)
                    f.write(ai_text)
                    f.write('\n')
                try:
                    return json.loads(ai_text)
                except:
                    # 解析失败就包装成回复格式
                    return {
                        "action": "answer_user",
                        "parameters": {"response": ai_text}
                    }
            else:
                raise Exception("API调用失败")

        except Exception as e:
            return {
                "action": "answer_user",
                "parameters": {"response": f"AI暂时不可用: {str(e)}"}
            }

    async def _execute_llm_action(self, action: Dict, db: Session, current_user: User) -> str:

        action_name = action.get("action")
        parameters = action.get("parameters")

        if not action_name or not parameters:
            return "AI返回格式错误，请重试。"

        logger.info(f"准备执行动作: {action_name}")

        try:
            if action_name == "answer_user":
                return parameters.get("response", "我不知道该说什么。")

                # ai_service.py -> _execute_llm_action 方法内

            elif action_name == "control_device":

                response_text = parameters.get("response", "设备已操作。")

                devices_to_control = parameters.get("devices", [])

                for device_op in devices_to_control:

                    device_id = device_op.get("device_id")

                    status = device_op.get("status")

                    action_type = device_op.get("action")

                    # 1. 查找设备

                    device = db.query(Device).filter(

                        Device.id == device_id,

                        Device.house_id == current_user.house_id

                    ).first()

                    # 2. 如果找到了设备，才执行所有操作

                    if device:

                        print(f"✅ 找到设备: {device.name}, 当前状态: {device.status}")

                        # 2.1 更新设备状态

                        if device.status:

                            device.status.update(status)

                        else:

                            device.status = status

                        # 【修正点1】: flag_modified 应在更新操作后、commit之前调用

                        # 无论status是新建还是更新，都标记为已修改

                        flag_modified(device, 'status')

                        device.is_online = True

                        print(f"🔧 更新后状态: {device.status}")

                        # 2.2 提交更改到数据库

                        db.commit()

                        print("✅ 数据库已提交")

                        # 【修正点2】: MQTT指令应该在数据库成功提交后，对已找到的设备发送

                        try:

                            from app.services.mqtt_service import mqtt_service

                            print(f"🚀 准备向设备 {device.device_id} 发送MQTT指令...")

                            mqtt_service.publish_device_control(device.device_id, {

                                "action": action_type,

                                "parameters": status

                            })

                            print("✅ MQTT指令已发送")

                        except Exception as mqtt_error:

                            logger.warning(f"MQTT发送失败: {mqtt_error}")


                    # 3. 如果没找到设备，就只打印日志

                    else:

                        print(f"❌ 未找到设备 ID: {device_id}")

                return response_text

            elif action_name == "execute_scene":
                scene_id = parameters.get("scene_id")

                # 查找并执行场景
                scene = db.query(Scene).filter(
                    Scene.id == scene_id,
                    Scene.house_id == current_user.house_id
                ).first()

                if scene:
                    # 执行场景中的所有动作
                    for action_data in scene.actions:
                        device_id = action_data.get("device_id")
                        device_params = action_data.get("parameters", {})

                        device = db.query(Device).filter(Device.id == device_id).first()
                        if device:
                            device.status = device_params
                            db.commit()

                    return parameters.get("response", f"场景 {scene.name} 已执行。")
                else:
                    return "未找到指定场景。"

            elif action_name == "create_scene":
                scene_data = parameters.get("scene_data")

                # 创建新场景
                new_scene = Scene(
                    name=scene_data.get("name"),
                    description=scene_data.get("description", ""),
                    house_id=current_user.house_id,
                    actions=scene_data.get("actions", []),
                    icon=scene_data.get("icon", "🤖"),
                    color=scene_data.get("color", "#2196F3"),
                    created_by=current_user.id
                )

                db.add(new_scene)
                db.commit()
                db.refresh(new_scene)

                return parameters.get("response", f"场景 {new_scene.name} 已创建。")

            elif action_name == "create_automation_rule":
                # 这里可以添加自动化规则创建逻辑
                return parameters.get("response", "自动化规则创建功能正在开发中。")

            else:
                logger.warning(f"接收到未知的动作: {action_name}")
                return "抱歉，我暂时无法执行这个操作。"

        except Exception as e:
            logger.error(f"执行动作时发生错误: {e}", exc_info=True)
            return f"执行操作时出现错误: {str(e)}"

    async def get_daily_summary(self, user: User, db: Session) -> str:
        """生成每日数据摘要"""
        try:
            yesterday = datetime.now() - timedelta(days=1)

            # 获取昨天的环境数据
            sensor_data = db.query(SensorData).filter(
                SensorData.house_id == user.house_id,
                SensorData.timestamp >= yesterday.date(),
                SensorData.timestamp < datetime.now().date()
            ).all()

            if not sensor_data:
                return f"😊 {user.username}，早上好！昨天没有收集到环境数据，今天是美好的一天！"

            # 计算统计数据
            temperatures = [d.temperature for d in sensor_data if d.temperature]
            humidities = [d.humidity for d in sensor_data if d.humidity]

            summary_parts = [f"😊 {user.username}，早上好！这是昨日的家庭环境摘要："]

            if temperatures:
                avg_temp = sum(temperatures) / len(temperatures)
                max_temp = max(temperatures)
                min_temp = min(temperatures)
                summary_parts.append(f"🌡️ 温度：平均{avg_temp:.1f}°C，最高{max_temp:.1f}°C，最低{min_temp:.1f}°C")

            if humidities:
                avg_humidity = sum(humidities) / len(humidities)
                summary_parts.append(f"💧 湿度：平均{avg_humidity:.1f}%")

            # 检查异常情况
            alerts = []
            for data in sensor_data:
                if data.flame_detected:
                    alerts.append("火焰警报")
                if data.gas_level and data.gas_level > 80:
                    alerts.append("可燃气体浓度过高")

            if alerts:
                summary_parts.append(f"⚠️ 异常事件：{', '.join(set(alerts))}")
            else:
                summary_parts.append("✅ 安全状况良好")

            summary_parts.append(f"📊 共记录{len(sensor_data)}条数据")
            summary_parts.append("🌟 祝您今天过得愉快！")

            return "\n".join(summary_parts)

        except Exception as e:
            logger.error(f"生成每日摘要时出错: {e}")
            return f"😊 {user.username}，早上好！今天是美好的一天！（数据摘要暂时无法生成）"

    def get_smart_suggestions(self, user: User, db: Session) -> List[str]:
        """获取智能建议"""
        suggestions = []
        current_hour = datetime.now().hour

        # 时间相关建议
        if 6 <= current_hour <= 8:
            suggestions.append("☀️ 早上好！要不要执行起床模式，开启美好的一天？")
        elif 11 <= current_hour <= 13:
            suggestions.append("🍽️ 午餐时间到了，要不要开启厨房照明？")
        elif 18 <= current_hour <= 20:
            suggestions.append("🏠 晚上好！是否需要执行回家模式？")
        elif 22 <= current_hour <= 24:
            suggestions.append("🌙 夜深了，要不要执行睡眠模式？")

        # 环境相关建议
        try:
            from sqlalchemy import desc
            latest_sensor = db.query(SensorData).filter(
                SensorData.house_id == user.house_id
            ).order_by(desc(SensorData.timestamp)).first()

            if latest_sensor:
                if latest_sensor.temperature and latest_sensor.temperature > 28:
                    suggestions.append("🌡️ 室内温度较高，建议调低空调温度")
                elif latest_sensor.temperature and latest_sensor.temperature < 18:
                    suggestions.append("❄️ 室内温度较低，建议调高空调温度")

                if latest_sensor.humidity and latest_sensor.humidity < 40:
                    suggestions.append("💧 空气有些干燥，建议开启加湿器")
                elif latest_sensor.humidity and latest_sensor.humidity > 70:
                    suggestions.append("💨 湿度较高，建议开启除湿功能")

                if latest_sensor.gas_level and latest_sensor.gas_level > 50:
                    suggestions.append("⚠️ 可燃气体浓度偏高，请注意通风安全")

        except Exception as e:
            logger.warning(f"获取环境建议时出错: {e}")

        # 默认建议
        if not suggestions:
            suggestions = [
                "💡 您可以尝试说'开客厅灯'来控制设备",
                "🎬 试试创建一个电影模式场景",
                "📊 问我'检查家里状况'来了解设备状态"
            ]

        return suggestions


# 全局AI服务实例
ai_service = AIService()