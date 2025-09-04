from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, date

from app.database import get_db
from app.services.schedule_service import ScheduleService
from app.schemas.schedule import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse, ScheduleListQuery,
    ScheduleCalendarResponse, BatchOperation
)

router = APIRouter()


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule_by_id(
        schedule_id: int,
        db: Session = Depends(get_db)
):
    """获取单个日程详情"""
    schedule_service = ScheduleService(db)
    schedule = schedule_service.get_schedule_by_id(schedule_id)

    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
        schedule_id: int,
        schedule_data: ScheduleUpdate,
        db: Session = Depends(get_db)
):
    """更新日程"""
    schedule_service = ScheduleService(db)
    updated_schedule = schedule_service.update_schedule(schedule_id, schedule_data)

    if not updated_schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    return updated_schedule


@router.delete("/{schedule_id}")
async def delete_schedule(
        schedule_id: int,
        db: Session = Depends(get_db)
):
    """删除日程"""
    schedule_service = ScheduleService(db)
    success = schedule_service.delete_schedule(schedule_id)

    if not success:
        raise HTTPException(status_code=404, detail="日程不存在")

    return {"message": "日程删除成功", "schedule_id": schedule_id}


@router.patch("/{schedule_id}/complete", response_model=ScheduleResponse)
async def toggle_schedule_complete(
        schedule_id: int,
        db: Session = Depends(get_db)
):
    """切换日程完成状态"""
    schedule_service = ScheduleService(db)
    updated_schedule = schedule_service.toggle_complete_status(schedule_id)

    if not updated_schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    return updated_schedule


@router.get("/calendar/{year}/{month}")
async def get_calendar_data(
        year: int,
        month: int,
        db: Session = Depends(get_db)
):
    """获取月历视图数据"""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="月份必须在1-12之间")

    if not (2020 <= year <= 2030):
        raise HTTPException(status_code=400, detail="年份必须在2020-2030之间")

    try:
        schedule_service = ScheduleService(db)
        calendar_data = schedule_service.get_calendar_data(year, month)
        return calendar_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取月历数据失败: {str(e)}")


@router.post("/batch")
async def batch_operations(
        batch_data: BatchOperation,
        db: Session = Depends(get_db)
):
    """批量操作日程"""
    try:
        schedule_service = ScheduleService(db)
        result = schedule_service.batch_operations(
            batch_data.schedule_ids,
            batch_data.operation,
            batch_data.data
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量操作失败: {str(e)}")


@router.get("/today/summary")
async def get_today_summary(
        db: Session = Depends(get_db)
):
    """获取今日日程摘要"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")

        query = ScheduleListQuery(
            start_date=today,
            end_date=today,
            page=1,
            size=50
        )

        schedule_service = ScheduleService(db)
        result = schedule_service.get_schedules_list(query)

        schedules = result["schedules"]

        summary = {
            "date": today,
            "total_count": len(schedules),
            "completed_count": sum(1 for s in schedules if s.completed),
            "pending_count": sum(1 for s in schedules if not s.completed),
            "high_priority_count": sum(1 for s in schedules if s.priority.value == "high"),
            "schedules": schedules[:5],  # 只返回前5个日程
            "has_more": len(schedules) > 5
        }

        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取今日摘要失败: {str(e)}")


@router.get("/upcoming/week")
async def get_upcoming_week(
        db: Session = Depends(get_db)
):
    """获取未来一周的日程"""
    try:
        from datetime import timedelta

        today = datetime.now().date()
        end_date = today + timedelta(days=7)

        query = ScheduleListQuery(
            start_date=today.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            completed=False,  # 只显示未完成的
            page=1,
            size=100
        )

        schedule_service = ScheduleService(db)
        result = schedule_service.get_schedules_list(query)

        return {
            "start_date": today.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "schedules": result["schedules"],
            "total_count": result["total"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取未来一周日程失败: {str(e)}")


@router.get("/statistics/overview")
async def get_statistics_overview(
        db: Session = Depends(get_db)
):
    """获取日程统计概览"""
    try:
        from datetime import timedelta

        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        schedule_service = ScheduleService(db)

        # 本周统计
        week_query = ScheduleListQuery(
            start_date=week_ago.strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d"),
            page=1,
            size=1000
        )
        week_result = schedule_service.get_schedules_list(week_query)
        week_schedules = week_result["schedules"]

        # 本月统计
        month_query = ScheduleListQuery(
            start_date=month_ago.strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d"),
            page=1,
            size=1000
        )
        month_result = schedule_service.get_schedules_list(month_query)
        month_schedules = month_result["schedules"]

        return {
            "week_stats": {
                "total": len(week_schedules),
                "completed": sum(1 for s in week_schedules if s.completed),
                "completion_rate": round(sum(1 for s in week_schedules if s.completed) / len(week_schedules) * 100,
                                         1) if week_schedules else 0
            },
            "month_stats": {
                "total": len(month_schedules),
                "completed": sum(1 for s in month_schedules if s.completed),
                "completion_rate": round(sum(1 for s in month_schedules if s.completed) / len(month_schedules) * 100,
                                         1) if month_schedules else 0
            },
            "priority_distribution": {
                "high": sum(1 for s in month_schedules if s.priority.value == "high"),
                "medium": sum(1 for s in month_schedules if s.priority.value == "medium"),
                "low": sum(1 for s in month_schedules if s.priority.value == "low")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取统计数据失败: {str(e)}")


@router.post("/", response_model=ScheduleResponse)
async def create_schedule(
        schedule_data: ScheduleCreate,
        db: Session = Depends(get_db)
):
    """创建新日程"""
    try:
        schedule_service = ScheduleService(db)
        new_schedule = schedule_service.create_schedule(schedule_data)
        return new_schedule
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建日程失败: {str(e)}")


@router.get("/", response_model=Dict[str, Any])
async def get_schedules(
        start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
        end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
        completed: Optional[bool] = Query(None, description="完成状态筛选"),
        priority: Optional[str] = Query(None, description="优先级筛选"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(50, ge=1, le=200, description="每页大小"),
        db: Session = Depends(get_db)
):
    """获取日程列表"""
    try:
        query = ScheduleListQuery(
            start_date=start_date,
            end_date=end_date,
            completed=completed,
            priority=priority,
            page=page,
            size=size
        )

        schedule_service = ScheduleService(db)
        result = schedule_service.get_schedules_list(query)

        return {
            "schedules": result["schedules"],
            "pagination": {
                "total": result["total"],
                "page": result["page"],
                "size": result["size"],
                "total_pages": result["total_pages"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取日程列表失败: {str(e)}")