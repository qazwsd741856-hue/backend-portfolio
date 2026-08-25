def test_admin_user(admin_user):
    assert admin_user.role=="admin"
    assert admin_user.is_active==True
    
def test_admin_login(admin_user,client):
    response=client.post("/users/login",data={"username":"admin@test.com","password":"123456"})
    
    assert response.status_code==200
    
    result = response.json()

    assert "access_token" in result
    assert result["token_type"] == "bearer"