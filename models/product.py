from sqlalchemy import Column,Integer,String
from database import Base
from sqlalchemy.orm import relationship

class Product(Base):
    
    __tablename__="Product"
    
    id=Column(Integer,primary_key=True)
    name=Column(String,nullable=False)
    price=Column(Integer,nullable=False)
    stock=Column(Integer,nullable=False)
    
    orders=relationship("Order",back_populates="product")