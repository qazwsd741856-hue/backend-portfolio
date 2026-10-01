from fastapi import APIRouter,Depends,HTTPException,Query,Path
from security import require_admin
from schemas.user import AdminUserReturn,UserRoleUpdate,UserStatusUpdate
from models.user import User
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Literal

admin_router=APIRouter(prefix="/admin",tags=["admin"],dependencies=[Depends(require_admin)])

@admin_router.get("/users",response_model=list[AdminUserReturn])
async def get_user(page:int=Query(1,ge=1),
                   name:str | None =None,
                   limit:int=Query(10,ge=1,le=100),
                   order_by:Literal["asc","desc"]="asc",
                   db:AsyncSession=Depends(get_db)):

    offset=(page-1)*limit    
    try:
        # users=db.query(User).all()
        stmt=select(User.id,
                    User.name,
                    User.email,
                    User.role,
                    User.is_active)
        if name is not None:
            stmt=stmt.where(User.name==name)
        if order_by=="desc":
            stmt=stmt.order_by(User.id.desc())
        else:
            stmt=stmt.order_by(User.id.asc())
        stmt=stmt.limit(limit).offset(offset)
        result=await db.execute(stmt)
        users=result.mappings().all()
        return users
    
    except SQLAlchemyError:
        raise HTTPException(status_code=500,detail="資料庫錯誤")
    
    
@admin_router.patch("/users/{id}/role",response_model=AdminUserReturn)
async def update_user_role(data:UserRoleUpdate,
                id:int=Path(gt=0),
                db:AsyncSession=Depends(get_db),
                admin:User=Depends(require_admin)):

    try:
        # user=db.query(User).filter(User.id==id).with_for_update().first()

        stmt=select(User).where(User.id==id).with_for_update()
        result= await db.execute(stmt)
        user=result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404,detail="找不到使用者")
        if user.id==admin.id:
            raise HTTPException(status_code=403,detail="無法更改自己權限")
        user.role=data.role
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError:
        await db.rollback() 
        raise HTTPException(status_code=500,detail="資料庫錯誤")

@admin_router.patch("/users/{id}/status",response_model=AdminUserReturn)
async def update_user_status(data:UserStatusUpdate,
                       db:AsyncSession=Depends(get_db),
                       id:int=Path(gt=0),
                       admin:User=Depends(require_admin)):
    try:
        # user=db.query(User).filter(User.id==id).with_for_update().first()

        stmt=select(User).where(User.id==id).with_for_update()
        result= await db.execute(stmt)
        user=result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404,detail="找不到使用者")
        if user.id==admin.id and data.is_active==False:
            raise HTTPException(status_code=403,detail="無法取得權限")
        user.is_active=data.is_active
        await db.commit()
        await db.refresh(user)
        return user
    except SQLAlchemyError:
        await db.rollback() 
        raise HTTPException(status_code=500,detail="資料庫錯誤")
