import os 
from dotenv import load_dotenv

load_dotenv(".env.test",override=False)
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")
REDIS_HOST=os.getenv("REDIS_HOST")
REDIS_DB = int(os.getenv("REDIS_DB", "1"))

os.environ["ASYNC_DATABASE_URL"] = (
    f"postgresql+asyncpg://"
    f"{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)


from sqlalchemy.pool import NullPool
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models.user import User
from models.product import Product
from security import hash_password
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
import pytest
from redis_client import get_redis
from redis.retry import Retry
from redis.backoff import NoBackoff
import redis.asyncio as redis
import redis as sync_redis


if POSTGRES_DB != "portfolio_test":
    raise RuntimeError(
        f"禁止執行測試：目前資料庫是 {POSTGRES_DB}，不是 portfolio_test"
    )

TEST_DATABASE_URL=f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
TEST_ASYNC_DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

test_engine = create_engine(TEST_DATABASE_URL)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    
)
test_async_engine = create_async_engine(TEST_ASYNC_DATABASE_URL,poolclass=NullPool)

AsyncTestSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_async_engine,
    expire_on_commit=False)


async def override_get_db():
    async with AsyncTestSessionLocal() as db:
      yield db

async def override_get_redis():
    test_redis_client = redis.Redis(
        host=REDIS_HOST,
        port=6379,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=1,
        socket_timeout=1,
        retry=Retry(NoBackoff(), 0)
    )

    try:
        yield test_redis_client
    finally:
        await test_redis_client.aclose()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis]= override_get_redis
# client=TestClient(app)

# @pytest.fixture()
# def client():
#     return TestClient(app)

@pytest.fixture()
def client():
    with TestClient(app) as client:
        yield client
@pytest.fixture()
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)
    
    
@pytest.fixture()
def admin_user(setup_database):
    db=TestSessionLocal()
    
    admin = User(
        name="Admin",
        email="admin@test.com",
        hashed_password=hash_password("123456"),
        role="admin",
        is_active=True
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    yield admin
    
    db.close()
@pytest.fixture()
def normal_user(setup_database):
    db=TestSessionLocal()
    user=User(name="User",
    email="user@test.com",
    hashed_password=hash_password("123456"),
    role="user",
    is_active=True)    
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    
    db.close()

@pytest.fixture()
def second_user(setup_database):
    db=TestSessionLocal()
    user=User(name="User2",
    email="user2@test.com",
    hashed_password=hash_password("123456"),
    role="user",
    is_active=True)    
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    
    db.close()    

@pytest.fixture()
def admin_token(admin_user,client):
    response = client.post(
        "/users/login",
        data={
            "username": "admin@test.com",
            "password": "123456"
        }
    )
    return response.json()["access_token"]    
@pytest.fixture()
def user_token(normal_user,client):
    response=client.post("/users/login",data={
        "username": "user@test.com",
        "password": "123456"
    })
    return response.json()["access_token"]
@pytest.fixture()
def second_user_token(second_user,client):
    response=client.post("/users/login",data={
        "username": "user2@test.com",
        "password": "123456"
    })
    return response.json()["access_token"]
@pytest.fixture()
def test_product(setup_database):
    db=TestSessionLocal()
    product=Product(name="keyboard",
                    price=2000,
                    stock=10)
    db.add(product)
    db.commit()
    db.refresh(product)
    
    yield product
    
    db.close()

@pytest.fixture(autouse=True)
def clean_test_redis():
    client = sync_redis.Redis(
        host=REDIS_HOST,
        port=6379,
        db=REDIS_DB,
        decode_responses=True,
    )

    client.flushdb()

    yield

    client.close()