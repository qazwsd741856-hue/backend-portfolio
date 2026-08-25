from conftest import TestSessionLocal
from models.product import Product
import pytest

def test_create_product(admin_token,client):
     response=client.post("/products",json={"name":"鍵盤","price":2000,"stock":10},headers={"Authorization":f"Bearer {admin_token}"})   
     
     assert response.status_code==201
     result =response.json()
     
     assert result["name"]=="鍵盤"
     assert result["price"]==2000
     assert result["stock"]==10
def test_create_product_by_user(user_token,client):
     response=client.post("/products",json={"name":"鍵盤","price":2000,"stock":10},headers={"Authorization":f"Bearer {user_token}"})   
     
     assert response.status_code==403
     result =response.json()
     
     assert result["detail"]=="需要管理者權限"
def test_create_product_by_none(setup_database,client):
    response=client.post("/products",json={"name":"鍵盤","price":2000,"stock":10})
    
    assert response.status_code == 401

def test_get_products(setup_database,client):
    response=client.get("/products")
    
    assert response.status_code == 200

def test_add_product(setup_database):
    db=TestSessionLocal()
    
    product = Product(
        name="滑鼠",
        price=1000,
        stock=10)
    db.add(product)
    db.commit()
    
    products=db.query(Product).all()
    
    assert len(products)==1
    
    db.close()

def test_database_is_empty(setup_database): 
    db=TestSessionLocal()
    
    products=db.query(Product).all()
    
    assert len(products)==0
    
    db.close()    

@pytest.mark.parametrize(
    "id",
    [0, -1, -100]
)
def test_get_product_invalid_id(id, client):
    response=client.get(f"/products/{id}")
    assert response.status_code==422