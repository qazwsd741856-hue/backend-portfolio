from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models.user import User
from models.product import Product
from security import hash_password
from fastapi.testclient import TestClient
import pytest


TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

TestSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine
)


def override_get_db():
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# client=TestClient(app)

@pytest.fixture()
def client():
    return TestClient(app)

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