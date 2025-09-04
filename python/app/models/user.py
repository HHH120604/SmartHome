from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    OWNER = "owner"
    MEMBER = "member"
    GUEST = "guest"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # phone = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(50), nullable=False)
    # hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.MEMBER)
    house_id = Column(Integer, nullable=True, default=1)
    # is_active = Column(Boolean, default=True)
    # guest_expire_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())