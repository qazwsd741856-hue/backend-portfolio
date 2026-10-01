from fastapi import APIRouter,HTTPException,Depends,Query,Path
# from database import get_connection
from redis_client import get_redis
from redis.exceptions import RedisError
from database import get_db
from schemas.product import ProductCreate ,ProductUpdate,ProductReturn,ProductPageReturn,ProductStockUpdate
from models.product import Product
from models.user import User
from security import require_admin
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError,IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from cache import delete_product_cache
from typing import Literal
import math
import json
import logging
# import sqlite3




logger=logging.getLogger(__name__)
product_router=APIRouter(prefix="/products",tags=["products"])



@product_router.get("",response_model=ProductPageReturn)
async def get_products(name:str | None=None,
                 min_stock:int | None =Query(None,ge=0),
                 min_price:int | None =Query(None,ge=0),
                 order:Literal["asc","desc"]="asc",
                 limit:int =Query(10,ge=1,le=100),
                 page:int =Query(1,ge=1),
                 db:AsyncSession=Depends(get_db)):
    try:
        offset=(page-1)*limit
        # query=db.query(Product)
        stmt=select(Product)
        if name is not None:
            # query=query.filter(Product.name==name)
            stmt=stmt.where(Product.name==name)
        if min_stock is not None:
            # query=query.filter(Product.stock>=min_stock)
            stmt=stmt.where(Product.stock>=min_stock)
        if min_price is not None:
            # query=query.filter(Product.price>=min_price)
            stmt=stmt.where(Product.price>=min_price)

        # total=query.count()
        count_stmt=select(func.count()).select_from(stmt.subquery())
        result=await db.execute(count_stmt)
        total=result.scalar_one()

        if order=="asc":
            # query=query.order_by(Product.price.asc())
            stmt=stmt.order_by(Product.price.asc())
        else:
            # query=query.order_by(Product.price.desc())
            stmt=stmt.order_by(Product.price.desc())
        
        pages=math.ceil(total/limit)
        # products=query.offset(offset).limit(limit).all()
        stmt=stmt.offset(offset).limit(limit)
        result=await db.execute(stmt)
        products=result.scalars().all()


    except SQLAlchemyError:
        logger.exception("取得商品列表時發生資料庫錯誤")
        raise HTTPException(status_code=500,detail="資料庫錯誤")
    return {"page":page,"limit":limit,"total":total,"total_pages":pages,"items":products}


# @product_router.get("/{id}",response_model=ProductReturn)
# def get_product(id: int=Path(gt=0),db:Session=Depends(get_db)):
#     try:
#         cache_key=f"product:{id}"
#         redis_available=True
#         try:
#             cached_product = redis_client.get(cache_key)
#         except RedisError:
#             logger.warning("Redis 目前無法讀取商品快取 %s", cache_key)
#             cached_product=None
#             redis_available=False

#         if cached_product is not None:
#             return json.loads(cached_product)

#         product=db.query(Product).filter(Product.id==id).first()

#         if product is None:
#             raise HTTPException(status_code=404,detail="未找到商品")
        
#         product_data = {
#             "id": product.id,
#             "name": product.name,
#             "price": product.price,
#             "stock": product.stock,
#             "description": product.description}  
#         if redis_available:
#             try:
#                 redis_client.set(cache_key,json.dumps(product_data),ex=300)
#             except RedisError:
#                 logger.warning("Redis目前無法寫入商品快取 %s", cache_key)
#         return product

#     except SQLAlchemyError:
#         logger.exception("取得商品時發生資料庫錯誤")
#         raise HTTPException(status_code=500, detail="資料庫錯誤")

@product_router.get("/{id}",response_model=ProductReturn)
async def get_product(id: int=Path(gt=0),db:AsyncSession=Depends(get_db)):
    try:
        cache_key=f"product:{id}"
        redis_available=True
        try:
            cached_product = await redis_client.get(cache_key)
        except RedisError:
            logger.warning("Redis 目前無法讀取商品快取 %s", cache_key)
            cached_product=None
            redis_available=False

        if cached_product is not None:
            return json.loads(cached_product)

        # product=db.query(Product).filter(Product.id==id).first()
        stmt=select(Product).where(Product.id==id)
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404,detail="未找到商品")
        
        product_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
            "description": product.description}  
        if redis_available:
            try:
                await redis_client.set(cache_key,json.dumps(product_data),ex=300)
            except RedisError:
                logger.warning("Redis目前無法寫入商品快取 %s", cache_key)
        return product

    except SQLAlchemyError:
        logger.exception("取得商品時發生資料庫錯誤")
        raise HTTPException(status_code=500, detail="資料庫錯誤")     
    



@product_router.post("", status_code=201,response_model=ProductReturn)
async def create_product(data: ProductCreate,
                   db:AsyncSession=Depends(get_db),
                   admin:User=Depends(require_admin)):
    try:
        product=Product(name=data.name,price=data.price,stock=data.stock,description=data.description)
        
        db.add(product)
        await db.commit()
        await db.refresh(product)
            
        return product
    
    except SQLAlchemyError:
        logger.exception("建立商品時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
        



@product_router.put("/{id}",response_model=ProductReturn)
async def update_product(data: ProductUpdate,
                   id: int=Path(gt=0),
                   db:AsyncSession=Depends(get_db),
                   admin:User=Depends(require_admin),
                   redis_client=Depends(get_redis)):
    try:
        # product=db.query(Product).filter(Product.id==id).with_for_update().first()
        stmt=select(Product).where(Product.id==id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404,detail="未找到商品")
            
        product.name=data.name
        product.price=data.price
        product.stock=data.stock
        product.description=data.description
        
        await db.commit()
        await delete_product_cache(redis_client,product.id)
        await db.refresh(product)
        
        return product
        
    
    except SQLAlchemyError:
        logger.exception("修改商品時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
   


@product_router.delete("/{id}")
async def delete_product(id: int=Path(gt=0),
                   db:AsyncSession=Depends(get_db),
                   admin:User=Depends(require_admin),
                   redis_client=Depends(get_redis)):
    try:
        # product=db.query(Product).filter(Product.id==id).with_for_update().first()
        stmt=select(Product).where(Product.id==id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()
        
        if product is None:
            raise HTTPException(status_code=404, detail="未找到商品")
        
        await db.delete(product)
        await db.commit()
        await delete_product_cache(redis_client,product.id)

        return {"message": "商品刪除成功"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409,detail="商品已有訂單紀錄，無法刪除")
    except SQLAlchemyError:
        logger.exception("刪除商品時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")             

@product_router.patch("/{id}/stock",response_model=ProductReturn)
async def update_product_stock(data:ProductStockUpdate,
                         id:int=Path(gt=0),
                         db:AsyncSession=Depends(get_db),
                         admin:User=Depends(require_admin),
                         redis_client=Depends(get_redis)):
    try:
        # product=db.query(Product).filter(Product.id==id).with_for_update().first()
        stmt=select(Product).where(Product.id==id).with_for_update()
        result=await db.execute(stmt)
        product=result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404,detail="未找到該商品")
        product.stock=product.stock+data.amount

        await db.commit()
        await delete_product_cache(redis_client,product.id)
        await db.refresh(product)
        return product
    except SQLAlchemyError:
        logger.exception("修改商品庫存時發生資料庫錯誤")
        await db.rollback()
        raise HTTPException(status_code=500, detail="資料庫錯誤")
