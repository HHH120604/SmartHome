from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserCreate(BaseModel):
    phone: str = Field(..., description="手机号")
    username: str = Field(..., description="用户名")
    password: str = Field(..., min_length=6, description="密码")
    house_id: Optional[int] = Field(1, description="房屋ID")
    is_owner: bool = Field(False, description="是否为房主")


class UserLogin(BaseModel):
    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    id: int
    phone: str
    username: str
    role: UserRole
    house_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    phone: Optional[str] = None


class GuestInvite(BaseModel):
    phone: str = Field(..., description="访客手机号")
    expire_hours: int = Field(24, description="权限有效期(小时)")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, description="用户名")
    is_active: Optional[bool] = Field(None, description="是否激活")