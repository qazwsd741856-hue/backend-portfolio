from fastapi import APIRouter,Request,Depends,Form
from fastapi.templating import Jinja2Templates
from sqlalchemy import text,select
from sqlalchemy.ext.asyncio import AsyncSession

from database import engine,get_db
from redis_client import redis_client
from models.product import Product
from models.user import User
from security import verify_password

demo_router=APIRouter()

templates=Jinja2Templates(directory="templates")

@demo_router.get("/")
async def dashboard(request:Request):
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
        db_status="Healthy"
    except Exception:
        db_status="Unhealthy"

    try:
        await redis_client.ping()
        redis_status="Healthy"
    except Exception:
        redis_status="Unhealthy"


    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "api_status": "Healthy",
            "db_status": db_status,
            "redis_status": redis_status,
        }
    )
@demo_router.get("/demo/products")
async def Products_page(request:Request,
                        db=Depends(get_db)):
    stmt=select(Product)
    result=await db.execute(stmt)
    products=result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "products":products
        }
    )

@demo_router.get("/demo/login")
async def login_page(request:Request):
    return templates.TemplateResponse(
        request,
        name="login.html"
    )

@demo_router.get("/demo/orders")
async def orders_page(request:Request):
    return templates.TemplateResponse(
        request,
        name="orders.html"
    )
@demo_router.get("/demo/admin")
async def admin_page(request:Request):
    return templates.TemplateResponse(
        request,
        name="admin.html"
    )
@demo_router.get("/demo/events")
async def events_page(request:Request):
    return templates.TemplateResponse(
        request,
        name="events.html"
    )
@demo_router.get("/demo/register")
async def register_page(request:Request):
    return templates.TemplateResponse(
        request,
        name="register.html"
    )