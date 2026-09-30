from conftest import TestSessionLocal
from models.product import Product
import pytest
from threading import Thread,Barrier

def test_create_product(admin_token,client):
     response=client.post("/products",json={"name":"鍵盤","price":2000,"stock":10,"description":"機械式鍵盤"},headers={"Authorization":f"Bearer {admin_token}"})   
     
     assert response.status_code==201
     result =response.json()
     
     assert result["name"]=="鍵盤"
     assert result["price"]==2000
     assert result["stock"]==10
     assert result["description"]=="機械式鍵盤"
     
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

def test_concurrent_order_and_add_stock(admin_token,client,test_product,user_token):
    barrier=Barrier(2)
    responses=[]

    def place_order():
        barrier.wait()
        response=client.post("/orders",
                             json={"product_id":test_product.id,"amount":3},
                             headers={"Authorization":f"Bearer {user_token}"})
        responses.append(response)

    def add_stock():
        barrier.wait()
        response=client.patch(f"/products/{test_product.id}/stock",
                              json={"amount":20},
                              headers={"Authorization":f"Bearer {admin_token}"})
        responses.append(response)
    thread1=Thread(target=place_order)
    thread2=Thread(target=add_stock)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()
    assert len(responses)==2
    status_code=[response.status_code for response in responses]
    status_code.sort()
    assert status_code==[200,201]

    db=TestSessionLocal()
    product=db.query(Product).filter(Product.id==test_product.id).first()

    assert product.stock==27
    db.close()


   
    