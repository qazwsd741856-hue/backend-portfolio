from sqlalchemy import Column,String,Integer,ForeignKey
from database import Base
from sqlalchemy.orm import relationship

class Order(Base):
    
    __tablename__="Orders"
    
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer,ForeignKey("User.id"),nullable=False)
    product_id=Column(Integer,ForeignKey("Product.id"),nullable=False)
    amount=Column(Integer,nullable=False)
    
    user=relationship("User",back_populates="orders")
    product=relationship("Product",back_populates="orders")
    