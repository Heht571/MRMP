from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_async_db
from app.core import security
from app.core.config import settings
from app.models.auth import User
from app.schemas.user import TokenPayload

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_async_db():
        yield session

async def get_current_user(
    db: AsyncSession = Depends(get_async_db),
    token: str = Depends(reusable_oauth2)
) -> User:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无法验证凭证",
        )
    
    result = await db.execute(select(User).where(User.id == token_data.sub))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user

def check_permissions(required_permission: str):
    """
    权限检查依赖
    支持通配符: instance:create 匹配 instance:create 或 instance:* 或 *
    """
    async def _check(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_async_db)
    ) -> User:
        if current_user.is_superuser:
            return current_user
            
        # 加载用户角色和权限
        # 注意: 这里的 User 模型需要能够加载 roles
        # 由于是 async，我们在获取 user 时可能没有 eager load roles
        # 这里为了简单，假设 user.roles 已经被加载或者重新查询
        # 实际生产中建议在 get_current_user 中使用 selectinload
        
        # 重新查询带上 roles
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.id == current_user.id)
        )
        user_with_roles = result.scalar_one()
        
        user_permissions = set()
        for role in user_with_roles.roles:
            if role.permissions:
                for p in role.permissions:
                    user_permissions.add(p)
        
        # 检查权限
        # 1. 精确匹配
        if required_permission in user_permissions:
            return current_user
            
        # 2. 通配符匹配 (simple implementation)
        # instance:create -> instance:* -> *
        parts = required_permission.split(":")
        if f"{parts[0]}:*" in user_permissions or "*" in user_permissions:
            return current_user
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"缺少权限: {required_permission}"
        )
        
    return _check
