from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, date, time
from app.models.schedule import Priority


class ScheduleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, description="日程标题")
    description: Optional[str] = Field(None, max_length=500, description="日程描述")
    date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="日期格式: YYYY-MM-DD")
    time: str = Field(..., pattern=r'^\d{2}:\d{2}$', description="时间格式: HH:MM")
    location: Optional[str] = Field(None, max_length=200, description="地点")
    priority: Priority = Field(Priority.MEDIUM, description="优先级")
    reminder: Optional[str] = Field(None, pattern=r'^(none|15|30|60|120)$', description="提醒时间(分钟)")

    @validator('date')
    def validate_date(cls, v):
        """验证日期格式并检查是否为有效日期"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('日期格式不正确或日期无效')
        return v

    @validator('time')
    def validate_time(cls, v):
        """验证时间格式"""
        try:
            datetime.strptime(v, '%H:%M')
        except ValueError:
            raise ValueError('时间格式不正确')
        return v


class ScheduleCreate(ScheduleBase):
    """创建日程的请求模型"""
    pass


class ScheduleUpdate(BaseModel):
    """更新日程的请求模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    time: Optional[str] = Field(None, pattern=r'^\d{2}:\d{2}$')
    location: Optional[str] = Field(None, max_length=200)
    priority: Optional[Priority] = None
    reminder: Optional[str] = Field(None, pattern=r'^(none|15|30|60|120)$')
    completed: Optional[bool] = None

    @validator('date')
    def validate_date(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('日期格式不正确或日期无效')
        return v

    @validator('time')
    def validate_time(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%H:%M')
            except ValueError:
                raise ValueError('时间格式不正确')
        return v


class ScheduleResponse(ScheduleBase):
    """返回给客户端的日程模型"""
    id: int
    completed: bool
    created_by: int
    house_id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScheduleListQuery(BaseModel):
    """日程列表查询参数"""
    start_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$', description="开始日期")
    end_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$', description="结束日期")
    completed: Optional[bool] = Field(None, description="完成状态筛选")
    priority: Optional[Priority] = Field(None, description="优先级筛选")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(50, ge=1, le=200, description="每页大小")


class ScheduleCalendarResponse(BaseModel):
    """月历视图响应模型"""
    date: str
    schedules: List[ScheduleResponse]
    total_count: int
    completed_count: int
    high_priority_count: int


class BatchOperation(BaseModel):
    """批量操作请求模型"""
    schedule_ids: List[int] = Field(..., min_items=1, description="日程ID列表")
    operation: str = Field(..., pattern=r'^(complete|delete|update_priority)$', description="操作类型")
    data: Optional[dict] = Field(None, description="操作参数")


# 重复日程相关schemas
class RecurringScheduleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    time: str = Field(..., pattern=r'^\d{2}:\d{2}$')
    location: Optional[str] = Field(None, max_length=200)
    priority: Priority = Field(Priority.MEDIUM)
    reminder: Optional[str] = Field(None, pattern=r'^(none|15|30|60|120)$')

    repeat_type: str = Field(..., pattern=r'^(daily|weekly|monthly|yearly)$', description="重复类型")
    repeat_interval: int = Field(1, ge=1, le=365, description="重复间隔")
    repeat_end_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$', description="重复结束日期")
    repeat_count: Optional[int] = Field(None, ge=1, le=1000, description="重复次数")
    weekdays: Optional[str] = Field(None, pattern=r'^[1-7](,[1-7])*$', description="重复的星期几")


class RecurringScheduleCreate(RecurringScheduleBase):
    start_date: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="开始日期")


class RecurringScheduleResponse(RecurringScheduleBase):
    id: int
    created_by: int
    house_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# 提醒相关schemas
class ReminderResponse(BaseModel):
    id: int
    schedule_id: int
    reminder_time: datetime
    is_sent: bool
    sent_at: Optional[datetime]
    reminder_type: str

    class Config:
        from_attributes = True