from fastapi import APIRouter,HTTPException,Depends,Request
from fastapi.security import OAuth2PasswordRequestForm
from database import get_db
from security import hash_password ,verify_password,create_access_token
from schemas.user import UserCreate,UserReturn
from models.user import User
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from redis_client import RATE_LIMIT_SCRIPT,get_redis
from redis.exceptions import RedisError
import logging

logger=logging.getLogger(__name__)

user_router=APIRouter(prefix="/users",tags=["users"])    
    

    

        
@user_router.post("", status_code=201,response_model=UserReturn)
async def create_user(data: UserCreate,db:AsyncSession=Depends(get_db)):
   
    try:
        user=User(name=data.name,email=data.email,hashed_password=hash_password(data.password))
    
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
        return user
    
    except IntegrityError as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=409, detail="email重複")
    except SQLAlchemyError as e:
        print(e)
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")

@user_router.post("/login")
async def login_user(request:Request,
            data: OAuth2PasswordRequestForm = Depends(),
            db:AsyncSession=Depends(get_db),
            redis_client=Depends(get_redis)):
    # user=db.query(User).filter(User.email==data.username).first()
    key=f"rate_limit:login:{request.client.host}"
    LOGIN_RATE_LIMIT = 10
    LOGIN_RATE_LIMIT_WINDOW = 60

    try:
     count,ttl=await redis_client.eval(RATE_LIMIT_SCRIPT,1,key,LOGIN_RATE_LIMIT_WINDOW)

     if count>LOGIN_RATE_LIMIT:
        raise HTTPException(status_code=429,detail=f"request too much,retry after {ttl} seconds",headers={"Retry-After":str(ttl)})
    except RedisError:
     logger.exception("Rate limiter unavailable, fail-open",extra={"endpoint":"/login","client_ip":request.client.host})

    stmt=select(User).where(User.email==data.username)
    result= await db.execute(stmt)
    user=result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401,detail="email or password error")
    
    if not verify_password(data.password,user.hashed_password):
        raise HTTPException(status_code=401,detail="email or password error")
    
    if user.is_active==False:
        raise HTTPException(status_code=403,detail="您的帳號已停權")
    token=create_access_token(data={"sub":str(user.id)})
    
    return {"access_token":token,"token_type":"bearer"}