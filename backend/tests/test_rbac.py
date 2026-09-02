"""RBAC: role-protected admin routes."""


def test_regular_user_cannot_access_admin_routes(client, make_user, auth_headers):
    user = make_user(role="USER")
    response = client.get("/api/v1/admin/users", headers=auth_headers(user))
    assert response.status_code == 403


def test_admin_can_access_admin_routes(client, make_user, auth_headers):
    admin = make_user(role="ADMIN")
    response = client.get("/api/v1/admin/users", headers=auth_headers(admin))
    assert response.status_code == 200


def test_unauthenticated_request_is_rejected(client):
    response = client.get("/api/v1/admin/users")
    assert response.status_code == 401


def test_admin_dashboard_summary_shape(client, make_user, auth_headers, db_session):
    from decimal import Decimal

    from app.models.goal import Goal

    admin = make_user(role="ADMIN")
    user = make_user(role="USER")
    goal = Goal(
        user_id=user.id,
        title="Dashboard Test Goal",
        category="General",
        target_amount=Decimal("100.00"),
        lock_type="EASY",
        status="ACTIVE",
    )
    db_session.add(goal)
    db_session.commit()

    response = client.get("/api/v1/admin/dashboard", headers=auth_headers(admin))
    assert response.status_code == 200
    body = response.json()
    for field in (
        "total_users",
        "active_users",
        "total_goals",
        "active_goals",
        "completed_goals",
        "total_saved_amount",
        "total_withdrawn_amount",
        "pending_kyc_count",
        "pending_withdrawal_count",
    ):
        assert field in body


def test_admin_can_update_kyc_status(client, make_user, auth_headers):
    admin = make_user(role="ADMIN")
    user = make_user(role="USER")

    response = client.patch(
        f"/api/v1/admin/users/{user.id}/kyc",
        json={"kyc_status": "VERIFIED"},
        headers=auth_headers(admin),
    )
    assert response.status_code == 200
    assert response.json()["kyc_status"] == "VERIFIED"
