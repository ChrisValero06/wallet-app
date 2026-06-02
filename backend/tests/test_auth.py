def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "email": "nuevo@example.com",
        "full_name": "Nuevo Usuario",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "nuevo@example.com"
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    resp = client.post("/api/auth/register", json={
        "email": registered_user["email"],
        "full_name": "Otro",
        "password": "password123",
    })
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "full_name": "Weak",
        "password": "123",
    })
    assert resp.status_code == 422


def test_login_success(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": registered_user["email"],
        "password": registered_user["password"],
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, registered_user):
    resp = client.post("/api/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post("/api/auth/login", json={
        "email": "noexiste@example.com",
        "password": "password123",
    })
    assert resp.status_code == 401


def test_logout(client, auth_headers):
    resp = client.post("/api/auth/logout", headers=auth_headers)
    assert resp.status_code == 200
    resp2 = client.get("/api/users/me", headers=auth_headers)
    assert resp2.status_code == 401


def test_get_profile(client, auth_headers, registered_user):
    resp = client.get("/api/users/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == registered_user["email"]


def test_get_profile_unauthenticated(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 403
