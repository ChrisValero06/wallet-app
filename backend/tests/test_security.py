import uuid
import pytest

BASE = "http://localhost:8000"

_RUN = uuid.uuid4().hex[:8]


def uid():
    return uuid.uuid4().hex[:12]


def email(tag="user"):
    return f"{tag}_{_RUN}_{uid()}@example.com"


def card():
    return f"4111{uid()}"


def register_and_login(client, em=None, password="Password123"):
    em = em or email()
    client.post(f"{BASE}/api/auth/register", json={
        "email": em, "full_name": "Test", "password": password
    })
    r = client.post(f"{BASE}/api/auth/login", json={"email": em, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def make_pm(client, headers, identifier=None, alias="Test"):
    return client.post(f"{BASE}/api/payment-methods", headers=headers, json={
        "type": "card", "alias": alias,
        "institution": "BBVA", "currency": "MXN",
        "identifier": identifier or card(),
    })



class TestXSS:
    xss_payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "javascript:alert(1)",
        "<svg onload=alert(1)>",
        '"><script>alert(document.cookie)</script>',
    ]

    def test_xss_in_alias_stored_as_plain_text(self, client_http, sec_headers):
        for payload in self.xss_payloads:
            r = make_pm(client_http, sec_headers, alias=payload)
            assert r.status_code in (201, 409), f"Error inesperado con XSS en alias: {r.status_code}"
            if r.status_code == 201:
                data = r.json()
                assert data["alias"] == payload, "El backend alteró el alias inesperadamente"

    def test_xss_in_institution_stored_as_plain_text(self, client_http, sec_headers):
        for payload in self.xss_payloads:
            r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
                "type": "card", "alias": f"Test {uid()}",
                "institution": payload,
                "currency": "MXN", "identifier": card(),
            })
            assert r.status_code in (201, 409)

    def test_xss_in_full_name_on_register(self, client_http):
        for payload in self.xss_payloads:
            r = client_http.post(f"{BASE}/api/auth/register", json={
                "email": email("xss"),
                "full_name": payload,
                "password": "Password123",
            })
            assert r.status_code == 201
            assert r.json()["full_name"] == payload

    def test_content_type_is_json_not_html(self, client_http):
        r = client_http.get(f"{BASE}/api/users/me")
        assert "application/json" in r.headers.get("content-type", "")



class TestSQLInjection:
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin'--",
        "1; SELECT * FROM payment_methods",
    ]

    def test_sqli_in_email_login(self, client_http):
        for payload in self.payloads:
            r = client_http.post(f"{BASE}/api/auth/login", json={
                "email": payload, "password": "anything"
            })
            assert r.status_code in (401, 422), f"SQLi posible con: {payload!r}"

    def test_sqli_in_alias(self, client_http, sec_headers):
        for payload in self.payloads:
            r = make_pm(client_http, sec_headers, alias=payload)
            assert r.status_code != 500, f"Error 500 con SQLi en alias: {payload!r}"



class TestSensitiveDataExposure:

    def test_password_not_in_register_response(self, client_http):
        r = client_http.post(f"{BASE}/api/auth/register", json={
            "email": email("expose"), "full_name": "Expose", "password": "Password123"
        })
        assert "Password123" not in r.text
        assert "hashed_password" not in r.text

    def test_full_card_number_not_in_response(self, client_http, sec_headers):
        c = card()
        r = make_pm(client_http, sec_headers, identifier=c)
        assert r.status_code == 201, f"No se creó el PM: {r.text}"
        assert c not in r.text, "Número completo de tarjeta expuesto en respuesta"
        assert c[-4:] in r.text  # solo últimos 4

    def test_full_clabe_not_in_response(self, client_http, sec_headers):
        clabe = f"03218{uid()}9"  # 18 dígitos únicos
        r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
            "type": "clabe", "alias": "Mi CLABE",
            "institution": "Banorte", "currency": "MXN",
            "identifier": clabe,
        })
        assert r.status_code == 201
        assert clabe not in r.text, "CLABE completa expuesta en respuesta"

    def test_identifier_masked_in_list(self, client_http, sec_headers):
        c = card()
        make_pm(client_http, sec_headers, identifier=c, alias="Masked Test")
        r = client_http.get(f"{BASE}/api/payment-methods", headers=sec_headers)
        assert c not in r.text



class TestJWTSecurity:

    def test_no_token_returns_403(self, client_http):
        r = client_http.get(f"{BASE}/api/users/me")
        assert r.status_code == 403

    def test_invalid_token_returns_401(self, client_http):
        r = client_http.get(f"{BASE}/api/users/me",
                            headers={"Authorization": "Bearer token.falso.aqui"})
        assert r.status_code == 401

    def test_none_algorithm_token(self, client_http):
        import base64
        header  = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(b'{"sub":"hacker","exp":9999999999}').rstrip(b"=").decode()
        fake_token = f"{header}.{payload}."
        r = client_http.get(f"{BASE}/api/users/me",
                            headers={"Authorization": f"Bearer {fake_token}"})
        assert r.status_code == 401, "alg=none aceptado — vulnerabilidad crítica"

    def test_tampered_payload(self, client_http, sec_headers):
        import base64, json
        token = sec_headers["Authorization"].split(" ")[1]
        parts = token.split(".")
        fake_payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "00000000-0000-0000-0000-000000000000",
                        "exp": 9999999999}).encode()
        ).rstrip(b"=").decode()
        tampered = f"{parts[0]}.{fake_payload}.{parts[2]}"
        r = client_http.get(f"{BASE}/api/users/me",
                            headers={"Authorization": f"Bearer {tampered}"})
        assert r.status_code == 401, "Token manipulado aceptado — vulnerabilidad crítica"

    def test_expired_token_rejected(self, client_http):
        import base64, json
        header  = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(
            json.dumps({"sub": "algoid", "exp": 1000000}).encode()
        ).rstrip(b"=").decode()
        fake_token = f"{header}.{payload}.firmafalsa"
        r = client_http.get(f"{BASE}/api/users/me",
                            headers={"Authorization": f"Bearer {fake_token}"})
        assert r.status_code == 401

    def test_logout_invalidates_token(self, client_http):
        headers = register_and_login(client_http, email("logout"))
        r1 = client_http.get(f"{BASE}/api/users/me", headers=headers)
        assert r1.status_code == 200
        client_http.post(f"{BASE}/api/auth/logout", headers=headers)
        r2 = client_http.get(f"{BASE}/api/users/me", headers=headers)
        assert r2.status_code == 401, "Token sigue válido tras logout"



class TestIDOR:

    def test_cannot_read_other_users_payment_method(self, client_http, sec_headers):
        r = make_pm(client_http, sec_headers, identifier=card(), alias="IDOR Test")
        assert r.status_code == 201, f"No se creó el PM: {r.text}"
        pm_id = r.json()["id"]

        headers_b = register_and_login(client_http, email("idor_read"))
        r2 = client_http.get(f"{BASE}/api/payment-methods/{pm_id}", headers=headers_b)
        assert r2.status_code == 403, "IDOR: usuario B puede ver PM de usuario A"

    def test_cannot_delete_other_users_payment_method(self, client_http, sec_headers):
        r = make_pm(client_http, sec_headers, identifier=card(), alias="IDOR Del")
        assert r.status_code == 201, f"No se creó el PM: {r.text}"
        pm_id = r.json()["id"]

        headers_b = register_and_login(client_http, email("idor_del"))
        r2 = client_http.delete(f"{BASE}/api/payment-methods/{pm_id}", headers=headers_b)
        assert r2.status_code == 403, "IDOR: usuario B puede eliminar PM de usuario A"

    def test_list_only_own_payment_methods(self, client_http, sec_headers):
        make_pm(client_http, sec_headers, identifier=card(), alias="Solo Mío")

        headers_b = register_and_login(client_http, email("list_spy"))
        r = client_http.get(f"{BASE}/api/payment-methods", headers=headers_b)
        assert r.status_code == 200
        assert r.json()["total"] == 0, "Usuario B ve PMs de usuario A"



class TestMassAssignment:

    def test_extra_fields_in_register_ignored(self, client_http):
        r = client_http.post(f"{BASE}/api/auth/register", json={
            "email": email("mass"),
            "full_name": "Mass",
            "password": "Password123",
            "is_active": False,
            "id": "hacker-uuid",
        })
        assert r.status_code == 201
        assert r.json()["is_active"] is True
        assert r.json()["id"] != "hacker-uuid"

    def test_extra_fields_in_payment_method_ignored(self, client_http, sec_headers):
        r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
            "type": "card", "alias": "Mass PM", "institution": "Test",
            "currency": "MXN", "identifier": card(),
            "user_id": "otro-usuario",
            "status": "active",
            "is_deleted": True,
        })
        assert r.status_code == 201
        assert r.json()["status"] == "active"



class TestDuplicates:

    def test_duplicate_email_rejected(self, client_http):
        em = email("dup")
        data = {"email": em, "full_name": "Dup", "password": "Password123"}
        r1 = client_http.post(f"{BASE}/api/auth/register", json=data)
        r2 = client_http.post(f"{BASE}/api/auth/register", json=data)
        assert r1.status_code == 201
        assert r2.status_code == 409

    def test_duplicate_payment_method_rejected(self, client_http, sec_headers):
        c = card()
        make_pm(client_http, sec_headers, identifier=c, alias="Original")
        r2 = make_pm(client_http, sec_headers, identifier=c, alias="Copia")
        assert r2.status_code == 409



class TestInputValidation:

    def test_invalid_email_rejected(self, client_http):
        r = client_http.post(f"{BASE}/api/auth/register", json={
            "email": "no-es-un-email", "full_name": "Test", "password": "Password123"
        })
        assert r.status_code == 422

    def test_short_password_rejected(self, client_http):
        r = client_http.post(f"{BASE}/api/auth/register", json={
            "email": email("short"), "full_name": "Test", "password": "123"
        })
        assert r.status_code == 422

    def test_invalid_currency_rejected(self, client_http, sec_headers):
        r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
            "type": "card", "alias": "Bad", "institution": "Test",
            "currency": "DOLARES",
            "identifier": "1234",
        })
        assert r.status_code == 422

    def test_invalid_type_rejected(self, client_http, sec_headers):
        r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
            "type": "bitcoin",
            "alias": "BTC", "institution": "Satoshi",
            "currency": "BTC", "identifier": "wallet123",
        })
        assert r.status_code == 422

    def test_empty_alias_rejected(self, client_http, sec_headers):
        r = client_http.post(f"{BASE}/api/payment-methods", headers=sec_headers, json={
            "type": "card", "alias": "   ",
            "institution": "BBVA", "currency": "MXN", "identifier": "1234",
        })
        assert r.status_code == 422



@pytest.fixture(scope="module")
def client_http():
    import httpx
    with httpx.Client(base_url=BASE, timeout=10) as c:
        yield c


@pytest.fixture(scope="module")
def sec_headers(client_http):
    return register_and_login(client_http, email("sec_main"))
