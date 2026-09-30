from fastapi import APIRouter,HTTPException,Depends,Query,Path
from database import get_db
from schemas.order import OrderCreate,OrderReturn,OrderUpdate
from sqlalchemy.orm import Session,selectinload
from models.order import Order
from models.product import Product
from models.user import User 
from models.outboxevent import OutboxEvent
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from security import get_current_user
from cache import delete_product_cache
from redis_client import get_redis
from context_var import request_id
from typing import Literal
import logging

logger=logging.getLogger(__name__)

orders_router=APIRouter(prefix="/orders",tags=["orders"])

@orders_router.get("",response_model=list[OrderReturn])
async def get_orders(page:int=Query(1,gt=0),
                     limit:int=Query(10,ge=1,le=100),
                     order_by:Literal["asc","desc"]="asc",
                     db:AsyncSession=Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    offset=(page-1)*limit
    try:
        # query=db.query(Order)
        stmt=select(Order).options(selectinload(Order.user),selectinload(Order.product))
        if current_user.role!="admin":
            # query=query.filter(Order.user_id==current_user.id)
            stmt=stmt.where(Order.user_id==current_user.id)
        # orders=query.all()
        if order_by == "desc":
            stmt=stmt.order_by(Order.id.desc()).limit(limit).offset(offset)
        else:
            stmt=stmt.order_by(Order.id.asc()).limit(limit).offset(offset)
        result=await db.execute(stmt)
        orders=result.scalars().all()
        return orders
        
    
    except SQLAlchemyError:
        logger.exception("取得訂單列表時發生資料庫錯誤")
        raise HTTPException(status_code=500, detail="資料庫錯誤")     

@orders_router.get("/{id}",response_model=OrderReturn)
async def get_order(id:int=Path(gt=0),
               db:AsyncSession=Depends(get_db),
               current_user: User = Depends(get_current_user)):
    try:
        # order=db.query(Order).filter(Order.id==id).first()
        stmt=select(Order).options(selectinload(Order.user),selectinload(Order.product)).where(Order.id==id)
        result=await db.execute(stmt)
        order=result.scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail="未找到該訂單")
        if current_user.role!="admin" and current_user.id != order.user_id:
            raise HTTPException(status_code=403, detail="非您的訂單")
        return order
    except SQLAlchemyError:
        logger.exception("取得訂單時發生資料庫錯誤")
        raise HTTPException(status_code=500, detail="資料庫錯誤") 


@orders_router.post("", status_code=201,response_model=OrderReturn)
async def create_order(data: OrderCreate,
                 db:AsyncSession=Depends(get_db),
                 current_user: User = Depends(get_current_user),
                 redis_client=Depends(get_redis)):

    try:
        # product=db.query(Product).filter(Product.id==data.product_id).with_for_update().first()
        stmt=select(Product).where(Product.id==data.product_id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(status_code=404, detail="未找到商品")
        
        if product.stock>=data.amount:
            order=Order(user_id=current_user.id,product_id=data.product_id,amount=data.amount)
            product.stock=product.stock-data.amount
            
            db.add(order)
            await db.flush()

            outboxevent=OutboxEvent(event_type="order_created",payload={"order_id":order.id,"request_id":request_id.get()})
            db.add(outboxevent)
            await db.commit()
            logger.info(f"Order created",extra={"order_id":order.id})

            await delete_product_cache(redis_client,product.id)

            stmt=select(Order).options(selectinload(Order.user),selectinload(Order.product)).where(Order.id==order.id)
            result=await db.execute(stmt)
            order=result.scalar_one()
            
            return order
        
        else:
            logger.warning(f"Insufficient stock: product_id={product.id},"f"requested={data.amount}, stock={product.stock}")
            raise HTTPException(status_code=400, detail=f"商品不足,餘額為{product.stock}")
        
    except IntegrityError:
        logger.exception("建立訂單時發生資料完整性錯誤")
        await db.rollback()
        raise HTTPException(status_code=400, detail="訂單資料不正確")
    except SQLAlchemyError:
        logger.exception("建立訂單時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")

@orders_router.delete("/{id}")
async def delete_order(db:AsyncSession=Depends(get_db),
                 id:int=Path(gt=0),
                 user:User=Depends(get_current_user),
                 redis_client=Depends(get_redis)):
    try:
        # order=db.query(Order).filter(Order.id==id).with_for_update().first()
        stmt=select(Order).where(Order.id==id).with_for_update()
        result=await db.execute(stmt)
        order=result.scalar_one_or_none()

        if order is None:
            raise HTTPException(status_code=404, detail="未找到該筆訂單")
        if order.user_id != user.id and user.role!="admin":
            raise HTTPException(status_code=403, detail="無權刪除此訂單")
        # product=db.query(Product).filter(Product.id==order.product_id).with_for_update().first()
        stmt=select(Product).where(Product.id==order.product_id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404, detail="商品未存在")
        product.stock= product.stock+order.amount
        
        await db.delete(order)
        await db.commit()

        await delete_product_cache(redis_client,product.id)

    except SQLAlchemyError:
        logger.exception("刪除訂單時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
    
    return {"message": "訂單刪除成功"}

@orders_router.put("/{id}",response_model=OrderReturn)
async def update_order(data:OrderUpdate,
                 db:AsyncSession=Depends(get_db),
                 id:int=Path(gt=0),
                 user:User=Depends(get_current_user),
                 redis_client=Depends(get_redis)):
    try:
        # order=db.query(Order).filter(Order.id==id).with_for_update().first()
        stmt=select(Order).where(Order.id==id).with_for_update()
        result=await db.execute(stmt)
        order=result.scalar_one_or_none()

        if order is None:
            raise HTTPException(status_code=404, detail="未找到該筆訂單")
        if order.user_id != user.id and user.role!="admin":
            raise HTTPException(status_code=403, detail="無權更改此訂單")
        # product=db.query(Product).filter(Product.id==order.product_id).with_for_update().first()
        stmt=select(Product).where(Product.id==order.product_id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()
        
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
        
        await db.commit()
        await delete_product_cache(redis_client,product.id)
        stmt=select(Order).options(selectinload(Order.user),selectinload(Order.product)).where(Order.id==order.id)
        result=await db.execute(stmt)
        order=result.scalar_one()
        return order
    
    except SQLAlchemyError:
        logger.exception("更改訂單時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
    

