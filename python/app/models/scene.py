from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.sql import func
from app.database import Base

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)  # 新增描述字段
    house_id = Column(Integer, nullable=False, default=1)
    actions = Column(JSON, nullable=False)  # 存储场景动作列表
    icon = Column(String(50), nullable=True, default="🏠")
    color = Column(String(20), nullable=True, default="#3498db")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SceneExecutionLog(Base):
    """场景执行日志"""
    __tablename__ = "scene_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    executed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    house_id = Column(Integer, nullable=False)
    execution_result = Column(JSON, nullable=False)  # 执行结果详情
    execution_time = Column(DateTime, default=func.now())
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

class Automation(Base):
    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    house_id = Column(Integer, nullable=False, default=1)
    conditions = Column(JSON, nullable=False)  # IF条件
    actions = Column(JSON, nullable=False)     # THEN动作
    condition_logic = Column(String(10), default="AND")  # AND/OR
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())

# 预设场景模板
class SceneTemplate(Base):
    """场景模板"""
    __tablename__ = "scene_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)  # 分类：生活、娱乐、安全等
    template_actions = Column(JSON, nullable=False)  # 模板动作
    icon = Column(String(50), nullable=True)
    color = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)  # 使用次数
    created_at = Column(DateTime, default=func.now())