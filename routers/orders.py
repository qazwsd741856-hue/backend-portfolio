from fastapi import APIRouter,HTTPException,Depends,Query,Path
from database import get_db
from schemas.order import OrderCreate,OrderReturn,OrderUpdate
from sqlalchemy.orm import Session
from models.order import Order
from models.product import Product
from models.user import User 
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from security import get_current_user

orders_router=APIRouter(prefix="/orders",tags=["orders"])



@orders_router.get("",response_model=list[OrderReturn])
def get_orders(db:Session=Depends(get_db),current_user: User = Depends(get_current_user)):
    try:
        query=db.query(Order)
        
        if current_user.role!="admin":
            query=query.filter(Order.user_id==current_user.id)
           
        orders=query.all()
        return orders
    
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=500, detail="資料庫錯誤")     

@orders_router.get("/{id}",response_model=OrderReturn)
def get_order(id:int=Path(gt=0),
               db:Session=Depends(get_db),
               current_user: User = Depends(get_current_user)):
    try:
        order=db.query(Order).filter(Order.id==id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="未找到該訂單")
        if current_user.role!="admin" and current_user.id != order.user_id:
            raise HTTPException(status_code=403, detail="非您的訂單")
        return order
    except SQLAlchemyError as e:
        print(e)
        raise HTTPException(status_code=500, detail="資料庫錯誤") 


@orders_router.post("", status_code=201,response_model=OrderReturn)
def create_order(data: OrderCreate,
                 db:Session=Depends(get_db),
                 current_user: User = Depends(get_current_user)):

    try:
        product=db.query(Product).filter(Product.id==data.product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="未找到商品")
        
        if product.stock>=data.amount:
            order=Order(user_id=current_user.id,product_id=data.product_id,amount=data.amount)
            product.stock=product.stock-data.amount
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            return order
        
        else:
            raise HTTPException(status_code=400, detail=f"商品不足,餘額為{product.stock}")
        
    except IntegrityError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=400, detail="訂單資料不正確")
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")

@orders_router.delete("/{id}")
def delete_order(db:Session=Depends(get_db),
                 id:int=Path(gt=0),
                 user:User=Depends(get_current_user)):
    try:
        order=db.query(Order).filter(Order.id==id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="未找到該筆訂單")
        if order.user_id != user.id and user.role!="admin":
            raise HTTPException(status_code=403, detail="無權刪除此訂單")
        product=db.query(Product).filter(Product.id==order.product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="商品未存在")
        product.stock= product.stock+order.amount
        
        db.delete(order)
        db.commit()
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
    
    return {"message": "訂單刪除成功"}

@orders_router.put("/{id}",response_model=OrderReturn)
def update_order(data:OrderUpdate,
                 db:Session=Depends(get_db),
                 id:int=Path(gt=0),
                 user:User=Depends(get_current_user),):
    try:
        order=db.query(Order).filter(Order.id==id).first()
        if order is None:
            raise HTTPException(status_code=404, detail="未找到該筆訂單")
        if order.user_id != user.id and user.role!="admin":
            raise HTTPException(status_code=403, detail="無權更改此訂單")
        product=db.query(Product).filter(Product.id==order.product_id).first()
        
        if product is None:
            raise HTTPException(status_code=404, detail="商品未存在")
        if data.amount>order.amount:
            if product.stock>=(data.amount-order.amount):
                product.stock=product.stock-(data.amount-order.amount)
                order.amount=data.amount
            else:
                raise HTTPException(status_code=400, detail=f"商品不足,餘額為{product.stock}")
        elif data.amount<order.amount:
            product.stock=product.stock-(data.amount-order.amount)
            order.amount=data.amount
        
        db.commit()
        db.refresh(order)
        return order
    
    except SQLAlchemyError as e:
        print(e)
        db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
    

