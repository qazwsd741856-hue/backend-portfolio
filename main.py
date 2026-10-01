from fastapi import FastAPI,Request
from logging_config import setup_logging
setup_logging()
from context_var import request_id
from uuid import uuid4
from routers.products import product_router
from routers.users import user_router
from routers.orders import orders_router
from routers.admin import admin_router
from sentry_config import setup_sentry
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import HTTPException

setup_sentry()

app = FastAPI(title="Backend Portfolio API")
app.include_router(product_router)
app.include_router(user_router)
app.include_router(orders_router)
app.include_router(admin_router)

instrumentator=Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.middleware("http")
async def set_middleware(request,call_next):

    current_request_id=str(uuid4())
    token=request_id.set(current_request_id)

    try:
        response=await call_next(request)
        response.headers["X-request-ID"]=current_request_id
        return response
    finally:
        request_id.reset(token)

@app.get("/client-test")
async def client_test(request: Request):
    return {
        "client_host": request.client.host,
        "client_port": request.client.port,
        "x_forwarded_for": request.headers.get("x-forwarded-for")
    }