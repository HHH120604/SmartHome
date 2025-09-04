from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
import calendar

from app.models.schedule import Schedule, ScheduleReminder, RecurringSchedule, Priority
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleListQuery, ScheduleResponse


class ScheduleService:
    def __init__(self, db: Session):
        self.db = db

    def create_schedule(self, schedule_data: ScheduleCreate) -> ScheduleResponse:
        """创建新日程（无用户限制）"""
        # 检查时间冲突
        conflicts = self._check_time_conflicts(
            schedule_data.date,
            schedule_data.time,
            exclude_id=None
        )

        if conflicts:
            print(f"⚠️ 时间冲突检测: {len(conflicts)} 个冲突日程")

        # 创建日程（移除用户相关字段）
        schedule_dict = schedule_data.dict()

        # 添加必要的默认值
        if 'created_by' not in schedule_dict:
            schedule_dict['created_by'] = 1  # 默认用户ID
        if 'house_id' not in schedule_dict:
            schedule_dict['house_id'] = 1  # 默认房屋ID

        db_schedule = Schedule(**schedule_dict)

        self.db.add(db_schedule)
        self.db.commit()
        self.db.refresh(db_schedule)

        # 创建提醒
        if schedule_data.reminder and schedule_data.reminder != "none":
            self._create_reminder(db_schedule, schedule_data.reminder)

        return ScheduleResponse.from_orm(db_schedule)

    def get_schedule_by_id(self, schedule_id: int) -> Optional[ScheduleResponse]:
        """根据ID获取日程（任何人都可以查看）"""
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        if schedule:
            return ScheduleResponse.from_orm(schedule)
        return None

    def update_schedule(self, schedule_id: int, schedule_data: ScheduleUpdate) -> Optional[ScheduleResponse]:
        """更新日程（任何人都可以更新）"""
        db_schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()

        if not db_schedule:
            return None

        # 检查时间冲突（如果更新了日期或时间）
        if schedule_data.date or schedule_data.time:
            new_date = schedule_data.date or db_schedule.date
            new_time = schedule_data.time or db_schedule.time

            conflicts = self._check_time_conflicts(
                new_date, new_time, exclude_id=schedule_id
            )
            if conflicts:
                print(f"⚠️ 更新时检测到时间冲突: {len(conflicts)} 个")

        # 更新字段
        update_data = schedule_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_schedule, field, value)

        db_schedule.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_schedule)

        # 更新提醒
        if 'reminder' in update_data:
            self._update_reminders(db_schedule, schedule_data.reminder)

        return ScheduleResponse.from_orm(db_schedule)

    def delete_schedule(self, schedule_id: int) -> bool:
        """删除日程（任何人都可以删除）"""
        db_schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()

        if not db_schedule:
            return False

        # 删除相关提醒
        self.db.query(ScheduleReminder).filter(
            ScheduleReminder.schedule_id == schedule_id
        ).delete()

        # 删除日程
        self.db.delete(db_schedule)
        self.db.commit()

        return True

    def get_schedules_list(self, query: ScheduleListQuery) -> Dict[str, Any]:
        """获取日程列表（显示所有日程）"""
        # 构建查询条件（移除用户限制）
        conditions = []

        if query.start_date:
            conditions.append(Schedule.date >= query.start_date)
        if query.end_date:
            conditions.append(Schedule.date <= query.end_date)
        if query.completed is not None:
            conditions.append(Schedule.completed == query.completed)
        if query.priority:
            conditions.append(Schedule.priority == query.priority)

        # 执行查询
        base_query = self.db.query(Schedule)
        if conditions:
            base_query = base_query.filter(and_(*conditions))

        # 计算总数
        total = base_query.count()

        # 分页和排序
        schedules = base_query.order_by(
            asc(Schedule.date),
            asc(Schedule.time)
        ).offset((query.page - 1) * query.size).limit(query.size).all()

        # 转换为Pydantic模型
        schedule_responses = [ScheduleResponse.from_orm(schedule) for schedule in schedules]

        return {
            "schedules": schedule_responses,
            "total": total,
            "page": query.page,
            "size": query.size,
            "total_pages": (total + query.size - 1) // query.size
        }

    def get_calendar_data(self, year: int, month: int) -> Dict[str, Any]:
        """获取月历视图数据（显示所有日程）"""
        # 计算月份的日期范围
        start_date = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        # 获取该月所有日程（无用户限制）
        schedules = self.db.query(Schedule).filter(
            and_(
                Schedule.date >= start_date.strftime('%Y-%m-%d'),
                Schedule.date <= end_date.strftime('%Y-%m-%d')
            )
        ).order_by(asc(Schedule.date), asc(Schedule.time)).all()

        # 按日期分组
        calendar_data = {}
        for schedule in schedules:
            date_key = schedule.date
            if date_key not in calendar_data:
                calendar_data[date_key] = {
                    "date": date_key,
                    "schedules": [],
                    "total_count": 0,
                    "completed_count": 0,
                    "high_priority_count": 0
                }

            # 转换为Pydantic模型
            schedule_response = ScheduleResponse.from_orm(schedule)
            calendar_data[date_key]["schedules"].append(schedule_response)
            calendar_data[date_key]["total_count"] += 1

            if schedule.completed:
                calendar_data[date_key]["completed_count"] += 1
            if schedule.priority == Priority.HIGH:
                calendar_data[date_key]["high_priority_count"] += 1

        return {
            "year": year,
            "month": month,
            "calendar_data": list(calendar_data.values()),
            "total_schedules": len(schedules),
            "summary": {
                "total_days_with_schedules": len(calendar_data),
                "total_schedules": len(schedules),
                "completed_schedules": sum(s.completed for s in schedules),
                "high_priority_schedules": sum(1 for s in schedules if s.priority == Priority.HIGH)
            }
        }

    def toggle_complete_status(self, schedule_id: int) -> Optional[ScheduleResponse]:
        """切换日程完成状态（任何人都可以操作）"""
        db_schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()

        if not db_schedule:
            return None

        db_schedule.completed = not db_schedule.completed
        db_schedule.completed_at = datetime.now() if db_schedule.completed else None
        db_schedule.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(db_schedule)

        return ScheduleResponse.from_orm(db_schedule)

    def batch_operations(self, schedule_ids: List[int], operation: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """批量操作日程（任何人都可以操作）"""
        # 获取所有指定的日程（无用户限制）
        schedules = self.db.query(Schedule).filter(Schedule.id.in_(schedule_ids)).all()

        if not schedules:
            return {"success": False, "message": "没有找到指定的日程", "affected_count": 0}

        affected_count = 0

        if operation == "complete":
            for schedule in schedules:
                schedule.completed = True
                schedule.completed_at = datetime.now()
                schedule.updated_at = datetime.now()
                affected_count += 1

        elif operation == "delete":
            # 删除相关提醒
            self.db.query(ScheduleReminder).filter(
                ScheduleReminder.schedule_id.in_([s.id for s in schedules])
            ).delete()

            # 删除日程
            for schedule in schedules:
                self.db.delete(schedule)
                affected_count += 1

        elif operation == "update_priority" and data and "priority" in data:
            new_priority = Priority(data["priority"])
            for schedule in schedules:
                schedule.priority = new_priority
                schedule.updated_at = datetime.now()
                affected_count += 1

        self.db.commit()

        return {
            "success": True,
            "message": f"批量{operation}操作成功",
            "affected_count": affected_count
        }

    def _check_time_conflicts(self, date_str: str, time_str: str, exclude_id: Optional[int] = None) -> List[Schedule]:
        """检查时间冲突（检查所有日程）"""
        conditions = [
            Schedule.date == date_str,
            Schedule.time == time_str,
            Schedule.completed == False  # 只检查未完成的日程
        ]

        if exclude_id:
            conditions.append(Schedule.id != exclude_id)

        return self.db.query(Schedule).filter(and_(*conditions)).all()

    def _create_reminder(self, schedule: Schedule, reminder_minutes: str):
        """创建提醒"""
        if reminder_minutes == "none":
            return

        # 计算提醒时间
        schedule_datetime = datetime.strptime(f"{schedule.date} {schedule.time}", "%Y-%m-%d %H:%M")
        reminder_time = schedule_datetime - timedelta(minutes=int(reminder_minutes))

        reminder = ScheduleReminder(
            schedule_id=schedule.id,
            reminder_time=reminder_time,
            reminder_type="notification"
        )

        self.db.add(reminder)
        self.db.commit()

    def _update_reminders(self, schedule: Schedule, new_reminder: Optional[str]):
        """更新提醒设置"""
        # 删除现有提醒
        self.db.query(ScheduleReminder).filter(
            ScheduleReminder.schedule_id == schedule.id
        ).delete()

        # 创建新提醒
        if new_reminder and new_reminder != "none":
            self._create_reminder(schedule, new_reminder)

        self.db.commit()

    def get_pending_reminders(self) -> List[ScheduleReminder]:
        """获取待发送的提醒"""
        now = datetime.now()
        return self.db.query(ScheduleReminder).join(Schedule).filter(
            and_(
                ScheduleReminder.reminder_time <= now,
                ScheduleReminder.is_sent == False,
                Schedule.completed == False  # 只提醒未完成的日程
            )
        ).all()

    def mark_reminder_sent(self, reminder_id: int):
        """标记提醒已发送"""
        reminder = self.db.query(ScheduleReminder).filter(ScheduleReminder.id == reminder_id).first()
        if reminder:
            reminder.is_sent = True
            reminder.sent_at = datetime.now()
            self.db.commit()