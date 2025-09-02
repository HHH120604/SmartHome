from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SceneAction(BaseModel):
    device_id: int = Field(..., description="设备ID")
    action: str = Field(..., description="动作类型", example="turn_on")
    parameters: Dict[str, Any] = Field(..., description="动作参数")

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": 1,
                "action": "turn_on",
                "parameters": {
                    "power": True,
                    "brightness": 80,
                    "color": "#FFFFFF"
                }
            }
        }


class SceneCreate(BaseModel):
    name: str = Field(..., description="场景名称", min_length=1, max_length=50)
    actions: List[SceneAction] = Field(..., description="场景动作列表", min_items=1)
    icon: Optional[str] = Field("🏠", description="场景图标")
    color: Optional[str] = Field("#3498db", description="场景颜色")
    description: Optional[str] = Field(None, description="场景描述", max_length=200)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "回家模式",
                "description": "回家时自动开启客厅灯和空调",
                "icon": "🏡",
                "color": "#e74c3c",
                "actions": [
                    {
                        "device_id": 1,
                        "action": "turn_on",
                        "parameters": {"power": True, "brightness": 80}
                    },
                    {
                        "device_id": 3,
                        "action": "turn_on",
                        "parameters": {"power": True, "temperature": 25}
                    }
                ]
            }
        }


class SceneUpdate(BaseModel):
    name: Optional[str] = Field(None, description="场景名称")
    actions: Optional[List[SceneAction]] = Field(None, description="场景动作列表")
    icon: Optional[str] = Field(None, description="场景图标")
    color: Optional[str] = Field(None, description="场景颜色")
    description: Optional[str] = Field(None, description="场景描述")


class SceneResponse(BaseModel):
    id: int
    name: str
    actions: List[Dict[str, Any]]
    icon: Optional[str]
    color: Optional[str]
    description: Optional[str] = None  # 添加默认值None
    created_by: int
    created_at: datetime
    device_count: Optional[int] = 0

    class Config:
        from_attributes = True


class SceneExecutionResult(BaseModel):
    scene_id: int
    scene_name: str
    success: bool
    executed_actions: List[Dict[str, Any]]
    failed_actions: List[Dict[str, Any]]
    execution_time: float  # 执行耗时（秒）
    total_devices: int
    success_count: int
    failed_count: int


# 自动化相关Schema
class AutomationCondition(BaseModel):
    type: str = Field(..., description="条件类型", example="time|sensor|device")
    device_id: Optional[str] = Field(None, description="设备ID（sensor/device类型需要）")
    parameter: str = Field(..., description="参数名", example="temperature")
    operator: str = Field(..., description="操作符", example=">|<|==")
    value: str = Field(..., description="目标值")


class AutomationCreate(BaseModel):
    name: str = Field(..., description="自动化名称")
    conditions: List[AutomationCondition] = Field(..., description="触发条件")
    actions: List[SceneAction] = Field(..., description="执行动作")
    condition_logic: str = Field("AND", description="条件逻辑", example="AND|OR")


class AutomationResponse(BaseModel):
    id: int
    name: str
    conditions: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    condition_logic: str
    is_active: bool
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True