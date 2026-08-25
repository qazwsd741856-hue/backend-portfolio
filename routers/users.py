from fastapi import APIRouter,HTTPException,Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from security import hash_password ,verify_password,create_access_token
from schemas.user import UserCreate,UserReturn
from models.user import User
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError,IntegrityError


user_router=APIRouter(prefix="/users",tags=["users"])    
    

    

        
@user_router.post("", status_code=201,response_model=UserReturn)
def create_user(data: UserCreate,db:Session=Depends(get_db)):
   
    try:
        user=User(name=data.name,email=data.email,hashed_password=hash_password(data.password))
    
        db.add(user)
        db.commit()
        db.refresh(user)
    
        return user
    
    except IntegrityError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=409, detail="email重複")
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")

@user_router.post("/login")
def login_user(data: OAuth2PasswordRequestForm = Depends(),
               db:Session=Depends(get_db)):
    user=db.query(User).filter(User.email==data.username).first()
    
    if user is None:
        raise HTTPException(status_code=401,detail="email or password error")
    
    if not verify_password(data.password,user.hashed_password):
        raise HTTPException(status_code=401,detail="email or password error")
    
    if user.is_active==False:
        raise HTTPException(status_code=403,detail="您的帳號已停權")
    token=create_access_token(data={"sub":str(user.id)})
    
    return {"access_token":token,"token_type":"bearer"}