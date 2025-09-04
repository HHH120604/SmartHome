from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class Priority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD 格式
    time = Column(String(5), nullable=False)  # HH:MM 格式
    location = Column(String(200), nullable=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    completed = Column(Boolean, default=False)
    reminder = Column(String(20), nullable=True)  # 提醒时间: "15", "30", "60", "none"

    # 关联信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    house_id = Column(Integer, nullable=False, default=1)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)


class ScheduleReminder(Base):
    """日程提醒记录表"""
    __tablename__ = "schedule_reminders"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    reminder_type = Column(String(20), default="notification")  # notification, email, sms
    created_at = Column(DateTime, default=func.now())


class RecurringSchedule(Base):
    """重复日程配置表"""
    __tablename__ = "recurring_schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    time = Column(String(5), nullable=False)  # HH:MM
    location = Column(String(200), nullable=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM)
    reminder = Column(String(20), nullable=True)

    # 重复配置
    repeat_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    repeat_interval = Column(Integer, default=1)  # 每N天/周/月/年
    repeat_end_date = Column(String(10), nullable=True)  # 重复结束日期
    repeat_count = Column(Integer, nullable=True)  # 重复次数限制
    weekdays = Column(String(20), nullable=True)  # 仅周重复时使用："1,2,3,4,5"

    # 关联信息
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    house_id = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())