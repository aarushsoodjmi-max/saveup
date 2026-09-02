"""Auth: OTP send/verify, JWT issuance, OTP expiry/attempts, rate limiting."""

import time

import jwt as pyjwt

from app.core.config import settings


def test_send_otp_returns_debug_otp_outside_production(client):
    response = client.post("/api/v1/auth/send-otp", json={"phone_number": "+15551234567"})
    assert response.status_code == 200
    body = response.json()
    assert body["debug_otp"] is not None
    assert len(body["debug_otp"]) == settings.otp_length


def test_send_otp_rejects_invalid_phone_number(client):
    response = client.post("/api/v1/auth/send-otp", json={"phone_number": "not-a-phone"})
    assert response.status_code == 422


def test_verify_otp_creates_new_user_and_issues_tokens(client):
    phone = "+15559876543"
    send_response = client.post("/api/v1/auth/send-otp", json={"phone_number": phone})
    otp = send_response.json()["debug_otp"]

    verify_response = client.post(
        "/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp, "name": "Ada Lovelace"}
    )
    assert verify_response.status_code == 200
    body = verify_response.json()
    assert body["is_new_user"] is True
    assert body["access_token"]
    assert body["refresh_token"]

    decoded = pyjwt.decode(body["access_token"], settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert decoded["type"] == "access"
    assert decoded["role"] == "USER"


def test_verify_otp_without_name_fails_for_new_user(client):
    phone = "+15551112222"
    send_response = client.post("/api/v1/auth/send-otp", json={"phone_number": phone})
    otp = send_response.json()["debug_otp"]

    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp})
    assert response.status_code == 422


def test_verify_otp_rejects_wrong_code(client):
    phone = "+15553334444"
    client.post("/api/v1/auth/send-otp", json={"phone_number": phone})

    response = client.post(
        "/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": "000000", "name": "Someone"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] in ("INVALID_OTP", "OTP_EXPIRED")


def test_verify_otp_rejects_expired_otp(client, monkeypatch):
    monkeypatch.setattr(settings, "otp_expire_seconds", 1)
    phone = "+15556667777"
    send_response = client.post("/api/v1/auth/send-otp", json={"phone_number": phone})
    otp = send_response.json()["debug_otp"]

    time.sleep(1.5)

    response = client.post(
        "/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp, "name": "Someone"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "OTP_EXPIRED"


def test_login_existing_user_does_not_require_name(client):
    phone = "+15558889999"
    otp1 = client.post("/api/v1/auth/send-otp", json={"phone_number": phone}).json()["debug_otp"]
    client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp1, "name": "Repeat User"})

    otp2 = client.post("/api/v1/auth/send-otp", json={"phone_number": phone}).json()["debug_otp"]
    response = client.post("/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp2})
    assert response.status_code == 200
    assert response.json()["is_new_user"] is False


def test_refresh_token_rotation_and_reuse_detection(client):
    phone = "+15550001111"
    otp = client.post("/api/v1/auth/send-otp", json={"phone_number": phone}).json()["debug_otp"]
    auth_body = client.post(
        "/api/v1/auth/verify-otp", json={"phone_number": phone, "otp": otp, "name": "Refresh Tester"}
    ).json()

    first_refresh = auth_body["refresh_token"]
    rotate_response = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert rotate_response.status_code == 200
    new_refresh = rotate_response.json()["refresh_token"]
    assert new_refresh != first_refresh

    # Reusing the rotated-out token must fail (compromise-detection).
    reuse_response = client.post("/api/v1/auth/refresh", json={"refresh_token": first_refresh})
    assert reuse_response.status_code == 401

    # And should have revoked the whole chain, including the token that
    # replaced it.
    second_use_of_new = client.post("/api/v1/auth/refresh", json={"refresh_token": new_refresh})
    assert second_use_of_new.status_code == 401


def test_otp_send_rate_limit(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_otp_per_hour", 2)
    monkeypatch.setattr(settings, "otp_resend_cooldown_seconds", 0)
    phone = "+15552223333"
    for _ in range(2):
        assert client.post("/api/v1/auth/send-otp", json={"phone_number": phone}).status_code == 200

    limited = client.post("/api/v1/auth/send-otp", json={"phone_number": phone})
    assert limited.status_code == 429
