from redis_client import get_redis
from redis import RedisError
from main import app
def test_admin_user(admin_user):
    assert admin_user.role=="admin"
    assert admin_user.is_active==True
    
def test_admin_login(admin_user,client):
    response=client.post("/users/login",data={"username":"admin@test.com","password":"123456"})
    
    assert response.status_code==200
    
    result = response.json()

    assert "access_token" in result
    assert result["token_type"] == "bearer"


def test_login_rate_limit_integration(client,setup_database):


    for _ in range(10):
        response = client.post(
            "/users/login",
            data={
                "username": "abc",
                "password": "123"
            })
        assert response.status_code == 401
        
    response = client.post(
                "/users/login",
                data={
                    "username": "abc",
                    "password": "123"
                })
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    
class BrokenRedis:
    async def eval(self, *args, **kwargs):
        raise RedisError("Redis unavailable")
def test_login_rate_limit_fail_open(client, normal_user):

    def override_broken_redis():
        return BrokenRedis()
    original_override = app.dependency_overrides[get_redis]
    app.dependency_overrides[get_redis] = override_broken_redis

    try:
        response = client.post(
            "/users/login",
            data={
                "username": "user@test.com",
                "password": "123456"
            }
        )

        assert response.status_code == 200

    finally:
        app.dependency_overrides[get_redis] =  original_override