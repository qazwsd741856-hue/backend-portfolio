from fastapi import APIRouter,Depends,HTTPException,Query,Path
from security import require_admin
from schemas.user import AdminUserReturn,UserRoleUpdate,UserStatusUpdate
from models.user import User
from database import get_db
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

admin_router=APIRouter(prefix="/admin",tags=["admin"],dependencies=[Depends(require_admin)])

@admin_router.get("/users",response_model=list[AdminUserReturn])
def get_user(db:Session=Depends(get_db)):
    try:
        users=db.query(User).all()
        return users
    
    except SQLAlchemyError:
        raise HTTPException(status_code=500,detail="資料庫錯誤")
    
    
@admin_router.patch("/users/{id}/role",response_model=AdminUserReturn)
def update_user_role(data:UserRoleUpdate,
                id:int=Path(gt=0),
                db:Session=Depends(get_db),
                admin:User=Depends(require_admin)):

    try:
        user=db.query(User).filter(User.id==id).first()
        if user is None:
            raise HTTPException(status_code=404,detail="找不到使用者")
        if user.id==admin.id:
            raise HTTPException(status_code=403,detail="無法更改自己權限")
        user.role=data.role
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback() 
        raise HTTPException(status_code=500,detail="資料庫錯誤")

@admin_router.patch("/users/{id}/status",response_model=AdminUserReturn)
def update_user_status(data:UserStatusUpdate,
                       db:Session=Depends(get_db),
                       id:int=Path(gt=0),
                       admin:User=Depends(require_admin)):
    try:
        user=db.query(User).filter(User.id==id).first()
        if user is None:
            raise HTTPException(status_code=404,detail="找不到使用者")
        if user.id==admin.id and data.is_active==False:
            raise HTTPException(status_code=403,detail="無法取得權限")
        user.is_active=data.is_active
        db.commit()
        db.refresh(user)
        return user
    except SQLAlchemyError:
        db.rollback() 
        raise HTTPException(status_code=500,detail="資料庫錯誤")
