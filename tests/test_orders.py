from conftest import TestSessionLocal,AsyncTestSessionLocal
from models.order import Order
from models.product import Product
from models.outboxevent import OutboxEvent
from database import get_db
from sqlalchemy.exc import SQLAlchemyError
from main import app
import pytest
from threading import Thread,Barrier

def test_create_order_commit_failure(
    user_token,
    test_product,
    client
):
    async def override_failure_db():
        async with AsyncTestSessionLocal() as db:
            
            async def broken_commit():
                raise SQLAlchemyError("commit failed")

            db.commit = broken_commit
            yield db

    original_override = app.dependency_overrides[get_db]
    app.dependency_overrides[get_db] = override_failure_db

    try:
        response = client.post(
            "/orders",
            json={
                "product_id": test_product.id,
                "amount": 3
            },
            headers={
                "Authorization": f"Bearer {user_token}"
            }
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "資料庫錯誤"

    finally:
        app.dependency_overrides[get_db] = original_override

    db = TestSessionLocal()

    product = db.query(Product).filter(
        Product.id == test_product.id
    ).first()

    orders = db.query(Order).filter(
        Order.product_id == test_product.id
    ).all()
    outbox_events = db.query(OutboxEvent).all()

    assert product.stock == 10
    assert len(orders) == 0
    assert len(outbox_events) == 0


    db.close()

def test_order_lifecycle(user_token,test_product,client):
    create_response=client.post("/orders",
                                json={"product_id":test_product.id,
                                      "amount":3},
                                headers={"Authorization":f"Bearer {user_token}"})
    assert create_response.status_code == 201
    order_id=create_response.json()["id"]

    db=TestSessionLocal()
    product=db.query(Product).where(Product.id==test_product.id).first()
    assert product.stock==7
    order=db.query(Order).where(Order.id==order_id).first()
    assert order.amount==3

    db.close()

    update_response=client.put(f"/orders/{order_id}",
                               json={"amount":5},
                               headers={"Authorization":f"Bearer {user_token}"})
    assert update_response.status_code==200
    db=TestSessionLocal()
    product=db.query(Product).where(Product.id==test_product.id).first()
    assert product.stock==5
    order=db.query(Order).where(Order.id==order_id).first()
    assert order.amount==5

    db.close()

    delete_response=client.delete(f"/orders/{order_id}",
                                  headers={"Authorization":f"Bearer {user_token}"})
    assert delete_response.status_code==200
    db=TestSessionLocal()
    product=db.query(Product).where(Product.id==test_product.id).first()
    assert product.stock==10
    order=db.query(Order).where(Order.id==order_id).first()
    assert order is None

    db.close()



def test_concurrent_create_order_multiple_requests(user_token,test_product,client):
    db=TestSessionLocal()
    
    product=db.query(Product).where(Product.id==test_product.id).first()
    product.stock=5
    db.commit()
    db.close()

    responses=[]
    errors=[]
    barrier=Barrier(10)

    def place_order():
            try:    
                barrier.wait()
    
                response=client.post("/orders",
                                    json={"product_id":test_product.id,"amount":1},
                                    headers={"Authorization":f"Bearer {user_token}"})
                responses.append(response)
            except Exception as e:
                errors.append(e)
    
    threads=[]
    for i in range(10):
        thread=Thread(target=place_order)
        threads.append(thread)
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(responses)==10
    assert errors==[]

    status_codes=[response.status_code for response in responses]
    status_codes.sort()
    assert status_codes==[201,201,201,201,201,400,400,400,400,400]

    db=TestSessionLocal()
    
    product = db.query(Product).filter(Product.id == test_product.id).first()
    orders = db.query(Order).filter(Order.product_id == test_product.id).all()
    
    assert product.stock == 0
    assert len(orders) == 5
    db.close()
    




def test_concurrent_create_order(user_token,test_product,client):
    db=TestSessionLocal()

    product=db.query(Product).filter(Product.id==test_product.id).first()
    product.stock=1
    db.commit()
    db.close()

    responses=[]
    errors=[]
    barrier=Barrier(2)
    
    def place_order():
        try:    
            barrier.wait()

            response=client.post("/orders",
                                json={"product_id":test_product.id,"amount":1},
                                headers={"Authorization":f"Bearer {user_token}"})
            responses.append(response)
        except Exception as e:
            errors.append(e)

    thread1=Thread(target=place_order)
    thread2=Thread(target=place_order)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    assert len(responses)==2
    assert errors==[]
    status_codes=[response.status_code for response in responses]
    status_codes.sort()
    assert status_codes==[201,400]

    db=TestSessionLocal()

    product = db.query(Product).filter(Product.id == test_product.id).first()
    orders = db.query(Order).filter(Order.product_id == test_product.id).all()

    assert product.stock == 0
    assert len(orders) == 1
    

    db.close()



def test_concurrent_update_order(user_token,test_product,client):
    response=client.post("/orders",json={"product_id":test_product.id,"amount":1},headers={"Authorization":f"Bearer {user_token}"})
    assert response.status_code==201
    order_id=response.json()["id"]

    responses=[]
    barrier=Barrier(2)

    def update_order(amount):
        barrier.wait()

        response=client.put(f"/orders/{order_id}",
                             json={"amount":amount},
                             headers={"Authorization":f"Bearer {user_token}"})
        responses.append(response)

    thread1=Thread(target=update_order,args=(5,))
    thread2=Thread(target=update_order,args=(3,))

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    assert len(responses)==2
    status_codes=[response.status_code for response in responses]
    status_codes.sort()
    assert status_codes==[200,200]

    db=TestSessionLocal()

    product = db.query(Product).filter(Product.id == test_product.id).first()
    order = db.query(Order).filter(Order.id == order_id).first()

    assert product.stock + order.amount == 10
    db.close()

def test_concurrent_delete_order(user_token,test_product,client):
    response=client.post("/orders",json={"product_id":test_product.id,"amount":2},headers={"Authorization":f"Bearer {user_token}"})
    assert response.status_code==201
    order_id=response.json()["id"]

    responses=[]
    barrier=Barrier(2)

    def delete_order():
        barrier.wait()

        response=client.delete(f"/orders/{order_id}",headers={"Authorization":f"Bearer {user_token}"})
        responses.append(response)

    thread1=Thread(target=delete_order)
    thread2=Thread(target=delete_order)

    thread1.start()
    thread2.start()

    thread1.join()
    thread2.join()

    assert len(responses)==2
    status_codes=[response.status_code for response in responses]
    status_codes.sort()
    assert status_codes==[200,404]

    db=TestSessionLocal()

    product = db.query(Product).filter(Product.id == test_product.id).first()
    order = db.query(Order).filter(Order.id == order_id).first()

    assert product.stock == 10
    assert order is None
    db.close()

def test_create_order(user_token,test_product,client):
    response=client.post("/orders",
                         json={"product_id":test_product.id,"amount":3},
                         headers={"Authorization":f"Bearer {user_token}"})
    assert response.status_code==201
    
    db = TestSessionLocal()

    product = db.query(Product).filter(
        Product.id == test_product.id
    ).first()

    assert product.stock == 7

    db.close()

def test_create_order_insufficient_stock(user_token,test_product,client):
    response=client.post("/orders",
                         json={"product_id":test_product.id,"amount":20},
                         headers={"Authorization":f"Bearer {user_token}"})
    assert response.status_code==400
    assert response.json()["detail"]=="商品不足,餘額為10"
    
    db = TestSessionLocal()

    product = db.query(Product).filter(
        Product.id == test_product.id
    ).first()

    assert product.stock == 10

    db.close()

def test_delete_order_restore_stock(user_token, test_product,client):

    create_response = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 3
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert create_response.status_code == 201

    result = create_response.json()

    order_id = result["id"]
    
    delete_response=client.delete(f"/orders/{order_id}",headers={
        "Authorization": f"Bearer {user_token}"
    })
    
    assert delete_response.status_code == 200
    assert delete_response.json()["message"]=="訂單刪除成功"
    
    db = TestSessionLocal()

    product = db.query(Product).filter(
        Product.id == test_product.id
    ).first()
    order=db.query(Order).filter(Order.id==order_id).first()
    assert product.stock == 10
    assert order is None

    db.close()
    
def test_update_order_increase(user_token, test_product,client):

    create_response = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 3
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":5},headers={"Authorization": f"Bearer {user_token}"})
    
    assert update_response.status_code==200
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()

    assert order.amount == 5
    assert product.stock == 5

    db.close()

def test_update_order_decrease(user_token, test_product,client):
    create_response = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 5
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":2},headers={"Authorization": f"Bearer {user_token}"})
    
    assert update_response.status_code==200
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()

    assert order.amount == 2
    assert product.stock == 8

    db.close()
    
def test_update_order_insufficient_stock(user_token, test_product,client):
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]    
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":20},headers={"Authorization": f"Bearer {user_token}"})
    
    assert update_response.status_code == 400
    assert update_response.json()["detail"] == "商品不足,餘額為7"
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()

    assert order.amount == 3
    assert product.stock == 7

    db.close()
    
    
def test_update_order_same_amount(user_token, test_product,client):
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)

    assert create_response.status_code == 201

    order_id = create_response.json()["id"]    
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":3},headers={"Authorization": f"Bearer {user_token}"})
    
    assert update_response.status_code == 200
    assert update_response.json()["amount"]==3
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()

    assert order.amount == 3
    assert product.stock == 7

    db.close()    
    
def test_delete_other_user_order(user_token,second_user_token,test_product,client): 
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)
    assert create_response.status_code == 201
    
    order_id = create_response.json()["id"]    
    
    delete_response = client.delete(f"/orders/{order_id}",headers={"Authorization": f"Bearer {second_user_token}"})
    
    assert delete_response.status_code==403
    assert delete_response.json()["detail"]=="無權刪除此訂單"
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()
    
    assert order is not None
    
    assert product.stock == 7
    
    db.close()

def test_delete_other_user_order_by_admin(user_token,admin_token,test_product,client): 
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)
    assert create_response.status_code == 201
    
    order_id = create_response.json()["id"]    
    
    delete_response = client.delete(f"/orders/{order_id}",headers={"Authorization": f"Bearer {admin_token}"})
    
    assert delete_response.status_code==200
    assert delete_response.json()["message"]=="訂單刪除成功"
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()
    
    assert order is  None
    
    assert product.stock == 10
    
    db.close()

def test_update_other_user_order(
    user_token,
    second_user_token,
    test_product,
    client
):
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)
    assert create_response.status_code == 201
    
    order_id = create_response.json()["id"]    
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":5},headers={"Authorization": f"Bearer {second_user_token}"})
    
    assert  update_response.status_code==403
    assert  update_response.json()["detail"]=="無權更改此訂單"
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()
    
    assert order.amount==3
    
    assert product.stock == 7
    
    db.close()    
    
def test_update_other_user_order_by_admin(
    user_token,
    admin_token,
    test_product,
    client
):
    create_response = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 3
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)
    assert create_response.status_code == 201
    
    order_id = create_response.json()["id"]    
    
    update_response = client.put(f"/orders/{order_id}",json={"amount":5},headers={"Authorization": f"Bearer {admin_token}"})
    
    assert  update_response.status_code==200
    assert  update_response.json()["amount"]==5
    
    db = TestSessionLocal()

    order = db.query(Order).filter(
    Order.id == order_id
    ).first()

    product = db.query(Product).filter(
    Product.id == test_product.id
    ).first()
    
    assert order.amount==5
    
    assert product.stock == 5
    
    db.close()        

def test_get_orders_only_own_orders(
    user_token,
    second_user_token,
    test_product,
    client
):
    create_response1 = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 2
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    create_response2 = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 3
        },
        headers={
            "Authorization": f"Bearer {second_user_token}"
        }
    )

    assert create_response1.status_code == 201
    assert create_response2.status_code == 201

    get_response = client.get(
        "/orders",
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert get_response.status_code == 200

    result = get_response.json()

    assert len(result) == 1
    assert result[0]["amount"] == 2

def test_get_orders_by_admin(
    user_token,
    second_user_token,
    admin_token,
    test_product
    ,client
):
    create_response1 = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 2
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    create_response2 = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": 3
        },
        headers={
            "Authorization": f"Bearer {second_user_token}"
        }
    )

    assert create_response1.status_code == 201
    assert create_response2.status_code == 201

    get_response = client.get(
        "/orders",
        headers={
            "Authorization": f"Bearer {admin_token}"
        }
    )

    assert get_response.status_code == 200

    result = get_response.json()

    assert len(result) == 2
    assert result[0]["amount"] == 2
    assert result[1]["amount"] == 3

def test_get_order_by_normal(
    user_token,
    second_user_token,
    test_product,
    client
):    
    create_response1 = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 2
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)    
    
    assert create_response1.status_code == 201
   
    order_id1 = create_response1.json()["id"] 
   
    
    get_response1=client.get(f"/orders/{order_id1}",headers={
        "Authorization": f"Bearer {user_token}"
    })
    assert get_response1.status_code==200
    get_response2=client.get(f"/orders/{order_id1}",headers={
        "Authorization": f"Bearer {second_user_token}"
    })
    assert get_response2.status_code==403
    assert get_response2.json()["detail"]=="非您的訂單"
    
def test_get_order_by_admin(
    user_token,
    admin_token,
    test_product,
    client
):    
    create_response1 = client.post(
    "/orders",
    json={
        "product_id": test_product.id,
        "amount": 2
    },
    headers={
        "Authorization": f"Bearer {user_token}"
    }
)     
    assert create_response1.status_code == 201
    
    order_id1 = create_response1.json()["id"] 
    
    get_response1=client.get(f"/orders/{order_id1}",headers={
        "Authorization": f"Bearer {user_token}"
    })
    assert get_response1.status_code==200
    get_response2=client.get(f"/orders/{order_id1}",headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert get_response2.status_code==200

@pytest.mark.parametrize(
    "invalid_amount",
    [0, -1, -100]
)
def test_create_order_invalid_amount(
    user_token,
    test_product,
    invalid_amount,
    client
):
    response = client.post(
        "/orders",
        json={
            "product_id": test_product.id,
            "amount": invalid_amount
        },
        headers={
            "Authorization": f"Bearer {user_token}"
        }
    )

    assert response.status_code == 422
    
def test_get_order_not_found(user_token,client):
    response=client.get("/orders/9999",headers={
        "Authorization": f"Bearer {user_token}"})    
    assert response.status_code == 404
    assert response.json()["detail"] == "未找到該訂單"

def test_delete_order_not_found(user_token,client):
    response=client.delete("/orders/9999",headers={
        "Authorization": f"Bearer {user_token}"})    
    assert response.status_code == 404
    assert response.json()["detail"] == "未找到該筆訂單"
    
def test_update_order_not_found(user_token,client):
    response=client.put("/orders/9999",headers={
        "Authorization": f"Bearer {user_token}"},json={"amount":5})    
    assert response.status_code == 404
    assert response.json()["detail"] == "未找到該筆訂單"    
@pytest.mark.parametrize(
    "url",
    ["/orders","/orders/9999"])
def test_get_order_without_login(url,client):
    response=client.get(url)
    assert response.status_code==401
@pytest.mark.parametrize("method,url",[("post","/orders"),("put","/orders/9999"),("delete","/orders/9999")])
def test_order_without_login(method, url,client):
    response=client.request(method,url)
    assert response.status_code==401