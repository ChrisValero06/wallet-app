PM_PAYLOAD = {
    "type": "card",
    "alias": "Mi Visa",
    "institution": "BBVA",
    "currency": "MXN",
    "identifier": "4111111111111234",
}


def test_create_payment_method(client, auth_headers):
    resp = client.post("/api/payment-methods", json=PM_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["alias"] == "Mi Visa"
    assert "1234" in data["identifier_masked"]
    assert "4111" not in data["identifier_masked"]


def test_create_duplicate_payment_method(client, auth_headers):
    client.post("/api/payment-methods", json=PM_PAYLOAD, headers=auth_headers)
    resp = client.post("/api/payment-methods", json=PM_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 409


def test_list_payment_methods(client, auth_headers):
    resp = client.get("/api/payment-methods", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "pages" in data


def test_get_payment_method_detail(client, auth_headers):
    create_resp = client.post("/api/payment-methods", json={
        **PM_PAYLOAD, "identifier": "4111111111115678", "alias": "Mi Mastercard"
    }, headers=auth_headers)
    pm_id = create_resp.json()["id"]

    resp = client.get(f"/api/payment-methods/{pm_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == pm_id


def test_get_nonexistent_payment_method(client, auth_headers):
    resp = client.get("/api/payment-methods/no-existe", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_payment_method(client, auth_headers):
    create_resp = client.post("/api/payment-methods", json={
        **PM_PAYLOAD, "identifier": "4111111111119999", "alias": "Para Borrar"
    }, headers=auth_headers)
    pm_id = create_resp.json()["id"]

    resp = client.delete(f"/api/payment-methods/{pm_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "inactive"

    list_resp = client.get("/api/payment-methods", headers=auth_headers)
    ids = [pm["id"] for pm in list_resp.json()["items"]]
    assert pm_id not in ids


def test_access_other_users_payment_method(client):
    client.post("/api/auth/register", json={
        "email": "otro@example.com", "full_name": "Otro", "password": "password123"
    })
    login_resp = client.post("/api/auth/login", json={
        "email": "otro@example.com", "password": "password123"
    })
    other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

    create_resp = client.post("/api/payment-methods", json={
        **PM_PAYLOAD, "identifier": "4111111111110001", "alias": "PM Otro"
    }, headers=other_headers)
    pm_id = create_resp.json()["id"]

    client.post("/api/auth/register", json={
        "email": "primero@example.com", "full_name": "Primero", "password": "password123"
    })
    login_resp2 = client.post("/api/auth/login", json={
        "email": "primero@example.com", "password": "password123"
    })
    first_headers = {"Authorization": f"Bearer {login_resp2.json()['access_token']}"}

    resp = client.get(f"/api/payment-methods/{pm_id}", headers=first_headers)
    assert resp.status_code == 403


def test_pagination(client, auth_headers):
    resp = client.get("/api/payment-methods?page=1&page_size=5", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 5


def test_unauthenticated_access(client):
    resp = client.get("/api/payment-methods")
    assert resp.status_code == 403
