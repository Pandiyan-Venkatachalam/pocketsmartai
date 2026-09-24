def test_user_registration_success(client):
    res = client.post("/api/auth/register", json={
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "SecurePassword99"
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "jane.doe@example.com"
    assert data["user"]["name"] == "Jane Doe"

def test_duplicate_email_registration_fails(client):
    res1 = client.post("/api/auth/register", json={
        "name": "Unique User",
        "email": "unique@example.com",
        "password": "Password123"
    })
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json={
        "name": "Another User",
        "email": "unique@example.com",
        "password": "Password456"
    })
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_login_success(client):
    client.post("/api/auth/register", json={
        "name": "Sam Login",
        "email": "sam.login@example.com",
        "password": "CorrectPassword123"
    })

    res = client.post("/api/auth/login", json={
        "email": "sam.login@example.com",
        "password": "CorrectPassword123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_invalid_password(client):
    client.post("/api/auth/register", json={
        "name": "Sam Fail",
        "email": "sam.fail@example.com",
        "password": "CorrectPassword123"
    })

    res = client.post("/api/auth/login", json={
        "email": "sam.fail@example.com",
        "password": "WrongPassword!"
    })
    assert res.status_code == 401
    assert "Invalid email or password" in res.json()["detail"]

def test_get_current_user_me(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "test.user@example.com"

def test_unauthenticated_request_fails(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
