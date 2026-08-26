from fastapi import FastAPI
from routers.products import product_router
from routers.users import user_router
from routers.orders import orders_router
from routers.admin import admin_router

app = FastAPI(title="Backend Portfolio API")
app.include_router(product_router)
app.include_router(user_router)
app.include_router(orders_router)
app.include_router(admin_router)

