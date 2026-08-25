from pydantic import BaseModel,ConfigDict
from typing import Literal

class UserCreate(BaseModel):
    name: str
    email: str
    password:str
    
class UserReturn(BaseModel):
    id:int
    name:str
    email:str    
    
    model_config=ConfigDict(from_attributes=True)
    
class UserLogin(BaseModel):
    email:str
    password:str    
    
class UserRoleUpdate(BaseModel):
    role:Literal["user","admin"]
    
class AdminUserReturn(BaseModel):
    id:int
    name:str
    email:str
    role:Literal["user","admin"]
    is_active:bool
    model_config=ConfigDict(from_attributes=True)

class UserStatusUpdate(BaseModel):
    is_active:bool