"""Auth endpointlari uchun testlar."""
from tests.conftest import register, auth


class TestRegister:
    def test_register_success(self, client):
        r = client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "email": "new@test.uz",
            "password": "password123",
        })
        assert r.status_code == 201
        data = r.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client):
        register(client, "user1", "same@test.uz")
        r = client.post("/api/v1/auth/register", json={
            "username": "user2", "email": "same@test.uz", "password": "pass123!",
        })
        assert r.status_code == 409
        assert "email" in r.json()["detail"].lower()

    def test_register_duplicate_username(self, client):
        register(client, "alice")
        r = client.post("/api/v1/auth/register", json={
            "username": "alice", "email": "other@test.uz", "password": "pass123!",
        })
        assert r.status_code == 409

    def test_register_short_password(self, client):
        r = client.post("/api/v1/auth/register", json={
            "username": "u", "email": "u@test.uz", "password": "123",
        })
        assert r.status_code == 422

    def test_register_invalid_email(self, client):
        r = client.post("/api/v1/auth/register", json={
            "username": "u", "email": "not-an-email", "password": "pass123!",
        })
        assert r.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        register(client, "alice", password="mypassword")
        r = client.post("/api/v1/auth/login", json={
            "email": "alice@test.uz", "password": "mypassword",
        })
        assert r.status_code == 200
        assert "access_token" in r.json()

    def test_login_wrong_password(self, client):
        register(client, "alice", password="correct")
        r = client.post("/api/v1/auth/login", json={
            "email": "alice@test.uz", "password": "wrong",
        })
        assert r.status_code == 401

    def test_login_unknown_email(self, client):
        r = client.post("/api/v1/auth/login", json={
            "email": "ghost@test.uz", "password": "pass",
        })
        assert r.status_code == 401


class TestMe:
    def test_get_me(self, client, user_token):
        r = client.get("/api/v1/auth/me", headers=auth(user_token))
        assert r.status_code == 200
        data = r.json()
        assert data["username"] == "buyer1"
        assert data["is_seller"] is False
        assert data["is_admin"] is False

    def test_get_me_no_auth(self, client):
        r = client.get("/api/v1/auth/me")
        assert r.status_code == 401

    def test_get_me_invalid_token(self, client):
        r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer fake.token.here"})
        assert r.status_code == 401

    def test_update_me(self, client, user_token):
        r = client.patch("/api/v1/auth/me",
                         json={"avatar_url": "https://cdn.test/avatar.jpg", "auto_reply": "Hi!"},
                         headers=auth(user_token))
        assert r.status_code == 200
        data = r.json()
        assert data["avatar_url"] == "https://cdn.test/avatar.jpg"
        assert data["auto_reply"] == "Hi!"

    def test_update_vacation_mode(self, client, seller_token):
        r = client.patch("/api/v1/auth/me",
                         json={"is_on_vacation": True},
                         headers=auth(seller_token))
        assert r.status_code == 200
        assert r.json()["is_on_vacation"] is True


class TestBecomeSeller:
    def test_become_seller(self, client, user_token):
        r = client.post("/api/v1/auth/me/become-seller", headers=auth(user_token))
        assert r.status_code == 200
        assert r.json()["is_seller"] is True

    def test_become_seller_twice(self, client, seller_token):
        r = client.post("/api/v1/auth/me/become-seller", headers=auth(seller_token))
        assert r.status_code == 400
