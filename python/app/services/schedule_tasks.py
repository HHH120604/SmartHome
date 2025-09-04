import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from app.database import SessionLocal
from app.models.schedule import Schedule, ScheduleReminder
from app.models.user import User
from app.services.schedule_service import ScheduleService
# from app.services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)


class ScheduleTaskManager:
    def __init__(self):
        self.running = False
        self.reminder_task = None

    async def start_background_tasks(self):
        """启动后台任务"""
        if self.running:
            return

        self.running = True
        logger.info("🕐 日程后台任务管理器启动")

        # 启动提醒任务
        self.reminder_task = asyncio.create_task(self._reminder_loop())

    async def stop_background_tasks(self):
        """停止后台任务"""
        self.running = False

        if self.reminder_task:
            self.reminder_task.cancel()
            try:
                await self.reminder_task
            except asyncio.CancelledError:
                pass

        logger.info("🛑 日程后台任务管理器停止")

    async def _reminder_loop(self):
        """提醒循环任务"""
        while self.running:
            try:
                await self._process_reminders()
                await asyncio.sleep(60)  # 每分钟检查一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"提醒任务处理异常: {e}")
                await asyncio.sleep(60)

    async def _process_reminders(self):
        """处理待发送的提醒"""
        db = SessionLocal()
        try:
            schedule_service = ScheduleService(db)

            # 获取待发送的提醒
            pending_reminders = schedule_service.get_pending_reminders()

            if not pending_reminders:
                return

            logger.info(f"📅 处理 {len(pending_reminders)} 个待发送提醒")

            for reminder in pending_reminders:
                await self._send_reminder(reminder, db)
                schedule_service.mark_reminder_sent(reminder.id)

        except Exception as e:
            logger.error(f"处理提醒时出错: {e}")
        finally:
            db.close()

    async def _send_reminder(self, reminder: ScheduleReminder, db):
        """发送单个提醒"""
        try:
            # 获取关联的日程和用户信息
            schedule = db.query(Schedule).filter(Schedule.id == reminder.schedule_id).first()
            if not schedule:
                logger.warning(f"提醒 {reminder.id} 关联的日程不存在")
                return

            user = db.query(User).filter(User.id == schedule.created_by).first()
            if not user:
                logger.warning(f"提醒 {reminder.id} 关联的用户不存在")
                return

            # 计算距离日程开始还有多长时间
            schedule_datetime = datetime.strptime(f"{schedule.date} {schedule.time}", "%Y-%m-%d %H:%M")
            now = datetime.now()
            time_until = schedule_datetime - now

            # 构建提醒消息
            if time_until.total_seconds() > 0:
                minutes_until = int(time_until.total_seconds() / 60)
                time_text = f"{minutes_until}分钟后" if minutes_until < 60 else f"{int(minutes_until / 60)}小时{minutes_until % 60}分钟后"
            else:
                time_text = "现在"

            reminder_message = {
                "type": "schedule_reminder",
                "title": "📅 日程提醒",
                "content": f"您有一个日程即将开始：{schedule.title}",
                "schedule": {
                    "id": schedule.id,
                    "title": schedule.title,
                    "date": schedule.date,
                    "time": schedule.time,
                    "location": schedule.location,
                    "priority": schedule.priority.value,
                    "time_until": time_text
                },
                "priority": "high" if schedule.priority.value == "high" else "medium",
                "timestamp": now.isoformat()
            }

            # 发送WebSocket通知
            success = await websocket_manager.send_to_user(user.id, reminder_message)

            if success:
                logger.info(f"✅ 提醒已发送: {schedule.title} -> 用户 {user.username}")
            else:
                # 用户离线，可以考虑其他通知方式
                logger.info(f"💤 用户离线，提醒暂存: {schedule.title} -> 用户 {user.username}")
                # 这里可以添加离线通知逻辑，比如邮件或短信

        except Exception as e:
            logger.error(f"发送提醒时出错: {e}")

    async def create_daily_summary_task(self):
        """每日摘要任务（可以在特定时间运行）"""
        db = SessionLocal()
        try:
            # 获取所有用户
            users = db.query(User).filter(User.is_active == True).all()

            for user in users:
                try:
                    summary = await self._generate_daily_summary(user, db)
                    if summary:
                        await websocket_manager.send_to_user(user.id, {
                            "type": "daily_schedule_summary",
                            "title": "📊 每日日程摘要",
                            "content": summary,
                            "timestamp": datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.error(f"为用户 {user.username} 生成每日摘要时出错: {e}")

        finally:
            db.close()

    async def _generate_daily_summary(self, user: User, db) -> str:
        """为用户生成每日摘要"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 获取今日日程
        today_schedules = db.query(Schedule).filter(
            Schedule.created_by == user.id,
            Schedule.date == today
        ).all()

        if not today_schedules:
            return None

        total_count = len(today_schedules)
        completed_count = sum(1 for s in today_schedules if s.completed)
        pending_count = total_count - completed_count
        high_priority_count = sum(1 for s in today_schedules if s.priority.value == "high")

        summary_parts = [
            f"今日日程摘要：",
            f"📋 总计 {total_count} 个日程",
            f"✅ 已完成 {completed_count} 个",
            f"⏳ 待完成 {pending_count} 个"
        ]

        if high_priority_count > 0:
            summary_parts.append(f"🔥 高优先级 {high_priority_count} 个")

        if pending_count > 0:
            # 添加接下来的日程
            next_schedules = [s for s in today_schedules if not s.completed]
            next_schedules.sort(key=lambda x: x.time)

            summary_parts.append(f"⏰ 接下来：{next_schedules[0].title} ({next_schedules[0].time})")

        completion_rate = round((completed_count / total_count) * 100, 1) if total_count > 0 else 0
        summary_parts.append(f"📊 完成率：{completion_rate}%")

        return "\n".join(summary_parts)

    async def cleanup_old_reminders(self):
        """清理过期的提醒记录"""
        db = SessionLocal()
        try:
            # 删除30天前的已发送提醒
            cutoff_date = datetime.now() - timedelta(days=30)

            deleted_count = db.query(ScheduleReminder).filter(
                ScheduleReminder.sent_at < cutoff_date,
                ScheduleReminder.is_sent == True
            ).delete()

            db.commit()

            if deleted_count > 0:
                logger.info(f"🧹 清理了 {deleted_count} 个过期提醒记录")

        except Exception as e:
            logger.error(f"清理提醒记录时出错: {e}")
        finally:
            db.close()

    async def check_overdue_schedules(self):
        """检查过期未完成的日程"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")

            # 查找今天已过期但未完成的日程
            overdue_schedules = db.query(Schedule).filter(
                Schedule.date == today,
                Schedule.time < current_time,
                Schedule.completed == False
            ).all()

            if not overdue_schedules:
                return

            logger.info(f"⏰ 发现 {len(overdue_schedules)} 个过期未完成日程")

            # 按用户分组发送通知
            user_overdue_map = {}
            for schedule in overdue_schedules:
                if schedule.created_by not in user_overdue_map:
                    user_overdue_map[schedule.created_by] = []
                user_overdue_map[schedule.created_by].append(schedule)

            for user_id, schedules in user_overdue_map.items():
                await self._send_overdue_notification(user_id, schedules, db)

        except Exception as e:
            logger.error(f"检查过期日程时出错: {e}")
        finally:
            db.close()

    async def _send_overdue_notification(self, user_id: int, schedules: List[Schedule], db):
        """发送过期日程通知"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return

            schedule_titles = [s.title for s in schedules[:3]]  # 最多显示3个
            more_text = f" 等 {len(schedules)} 个日程" if len(schedules) > 3 else ""

            message = {
                "type": "overdue_schedules",
                "title": "⏰ 过期日程提醒",
                "content": f"您有以下日程已过期未完成：{', '.join(schedule_titles)}{more_text}",
                "schedules": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "time": s.time,
                        "priority": s.priority.value
                    }
                    for s in schedules
                ],
                "priority": "medium",
                "timestamp": datetime.now().isoformat()
            }

            await websocket_manager.send_to_user(user_id, message)
            logger.info(f"📨 过期日程通知已发送给用户 {user.username}")

        except Exception as e:
            logger.error(f"发送过期通知时出错: {e}")


# 全局任务管理器实例
schedule_task_manager = ScheduleTaskManager()