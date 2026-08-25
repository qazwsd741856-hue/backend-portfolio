from sqlalchemy import Column,String,Integer,Boolean
from database import Base
from sqlalchemy.orm import relationship

class User(Base):
    
    __tablename__="User"
    
    id=Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    email=Column(String,nullable=False,unique=True)
    hashed_password=Column(String,nullable=False)
    role=Column(String,nullable=False,default="user")
    is_active=Column(Boolean,nullable=False,default=True)
    
    orders=relationship("Order",back_populates="user")