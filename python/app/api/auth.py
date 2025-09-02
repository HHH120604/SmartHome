from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, Token, UserResponse, GuestInvite
from app.utils.security import verify_password, get_password_hash, create_access_token
from jose import JWTError, jwt
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户是否已存在
    db_user = db.query(User).filter(User.phone == user.phone).first()
    if db_user:
        raise HTTPException(status_code=400, detail="手机号已注册")

    # 创建新用户
    hashed_password = get_password_hash(user.password)
    db_user = User(
        phone=user.phone,
        username=user.username,
        hashed_password=hashed_password,
        role=UserRole.OWNER if user.is_owner else UserRole.MEMBER,
        house_id=user.house_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """用户登录"""
    user = db.query(User).filter(User.phone == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查访客权限是否过期
    if user.role == UserRole.GUEST and user.guest_expire_time:
        if datetime.now() > user.guest_expire_time:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="访客权限已过期"
            )

    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.phone}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="认证失败",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.phone == phone).first()
    if user is None:
        raise credentials_exception
    return user


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@router.post("/invite-guest")
async def invite_guest(
        guest_invite: GuestInvite,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """邀请访客"""
    if current_user.role not in [UserRole.OWNER, UserRole.MEMBER]:
        raise HTTPException(status_code=403, detail="只有房主和家庭成员可以邀请访客")

    # 检查用户是否已存在
    existing_user = db.query(User).filter(User.phone == guest_invite.phone).first()
    if existing_user:
        # 如果是已存在用户，更新为访客权限
        existing_user.role = UserRole.GUEST
        existing_user.house_id = current_user.house_id
        existing_user.guest_expire_time = datetime.now() + timedelta(hours=guest_invite.expire_hours)
        db.commit()
        return {"message": "访客权限已更新", "phone": guest_invite.phone, "expire_hours": guest_invite.expire_hours}
    else:
        # 创建新的访客用户
        guest_user = User(
            phone=guest_invite.phone,
            username=f"访客_{guest_invite.phone[-4:]}",  # 使用手机号后4位作为用户名
            hashed_password=get_password_hash("123456"),  # 默认密码
            role=UserRole.GUEST,
            house_id=current_user.house_id,
            guest_expire_time=datetime.now() + timedelta(hours=guest_invite.expire_hours)
        )
        db.add(guest_user)
        db.commit()
        return {"message": "访客邀请成功", "phone": guest_invite.phone, "default_password": "123456",
                "expire_hours": guest_invite.expire_hours}


@router.delete("/remove-guest/{phone}")
async def remove_guest(
        phone: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """移除访客"""
    if current_user.role not in [UserRole.OWNER, UserRole.MEMBER]:
        raise HTTPException(status_code=403, detail="只有房主和家庭成员可以移除访客")

    guest = db.query(User).filter(
        User.phone == phone,
        User.house_id == current_user.house_id,
        User.role == UserRole.GUEST
    ).first()

    if not guest:
        raise HTTPException(status_code=404, detail="访客不存在")

    db.delete(guest)
    db.commit()

    return {"message": "访客已移除", "phone": phone}