from pwdlib import PasswordHash
from datetime import datetime,timedelta,timezone
from fastapi.security import OAuth2PasswordBearer
import jwt
from fastapi import Depends,HTTPException
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy.exc import SQLAlchemyError
from models.user import User
import os 
from dotenv import load_dotenv

password_hash=PasswordHash.recommended()

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
if SECRET_KEY is None:
    raise RuntimeError("SECRET_KEY未設定")

ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/users/login"
)

def get_current_user(token:str=Depends(oauth2_scheme),db:Session=Depends(get_db)):
    try:
        payload = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM])

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
            status_code=401,
            detail="Token 無效")

    except jwt.PyJWTError:
        raise HTTPException(status_code=401,detail="Token 無效")
        
    try:
        user=db.query(User).filter(User.id==user_id).first()
        
        if user is None:
            raise HTTPException(status_code=401,detail="Token 無效")
        if user.is_active==False:
            raise HTTPException(status_code=403,detail="帳號已停權")
    except SQLAlchemyError:
        raise HTTPException(status_code=500,detail="資料庫錯誤")
    
    return user

def require_admin(user:User=Depends(get_current_user)):
    if user.role != "admin":
     raise HTTPException(status_code=403,detail="需要管理者權限")
     
    return user
    
def create_access_token(data:dict):
    
    to_encode=data.copy()
    
    expire=datetime.now(timezone.utc)+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp":expire})
    
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)

def hash_password(password:str):
    
    return password_hash.hash(password)

def verify_password(user_password:str,db_password:str):
    
    return password_hash.verify(user_password,db_password)

