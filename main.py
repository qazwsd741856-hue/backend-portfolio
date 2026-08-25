from fastapi import FastAPI
from database import init_db
from routers.products import product_router
from routers.users import user_router
from routers.orders import orders_router
from routers.admin import admin_router
from database import engine,Base
from models.product import Product
from models.user import User
from models.order import Order

# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Backend Portfolio API")
app.include_router(product_router)
app.include_router(user_router)
app.include_router(orders_router)
app.include_router(admin_router)

Base.metadata.create_all(bind=engine)

init_db()

