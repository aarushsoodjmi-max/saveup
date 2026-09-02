"""Goal CRUD, validation, and status transitions."""

from decimal import Decimal


def _create_goal(client, headers, **overrides):
    payload = {
        "title": "New Laptop",
        "category": "Electronics",
        "target_amount": "50000.00",
        "lock_type": "EASY",
        **overrides,
    }
    return client.post("/api/v1/goals", json=payload, headers=headers)


def test_create_goal(client, make_user, auth_headers):
    user = make_user()
    response = _create_goal(client, auth_headers(user))
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "New Laptop"
    assert body["status"] == "ACTIVE"
    assert body["saved_amount"] == "0.00"
    assert body["progress_percentage"] == 0.0


def test_create_goal_rejects_non_positive_amount(client, make_user, auth_headers):
    user = make_user()
    response = _create_goal(client, auth_headers(user), target_amount="0")
    assert response.status_code == 422


def test_create_goal_rejects_invalid_lock_type(client, make_user, auth_headers):
    user = make_user()
    response = _create_goal(client, auth_headers(user), lock_type="SUPER_HARD")
    assert response.status_code == 422


def test_list_goals_only_returns_own_goals(client, make_user, auth_headers):
    owner = make_user()
    other = make_user()
    _create_goal(client, auth_headers(owner))
    _create_goal(client, auth_headers(other), title="Someone Else's Goal")

    response = client.get("/api/v1/goals", headers=auth_headers(owner))
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["title"] == "New Laptop"


def test_get_goal_not_found_for_other_user(client, make_user, auth_headers):
    owner = make_user()
    other = make_user()
    goal_id = _create_goal(client, auth_headers(owner)).json()["id"]

    response = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers(other))
    assert response.status_code == 404


def test_update_goal_target_below_saved_amount_rejected(client, make_user, auth_headers, db_session):
    from app.services.ledger_service import LedgerService

    user = make_user()
    goal_id = _create_goal(client, auth_headers(user), target_amount="1000.00").json()["id"]

    LedgerService(db_session).deposit(user=user, goal_id=goal_id, amount=Decimal("500.00"))

    response = client.put(
        f"/api/v1/goals/{goal_id}", json={"target_amount": "100.00"}, headers=auth_headers(user)
    )
    assert response.status_code == 422


def test_pause_resume_goal(client, make_user, auth_headers):
    user = make_user()
    goal_id = _create_goal(client, auth_headers(user)).json()["id"]

    paused = client.patch(f"/api/v1/goals/{goal_id}/pause", headers=auth_headers(user))
    assert paused.status_code == 200
    assert paused.json()["status"] == "PAUSED"

    resumed = client.patch(f"/api/v1/goals/{goal_id}/resume", headers=auth_headers(user))
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "ACTIVE"


def test_delete_goal_with_balance_rejected(client, make_user, auth_headers, db_session):
    from app.services.ledger_service import LedgerService

    user = make_user()
    goal_id = _create_goal(client, auth_headers(user)).json()["id"]
    LedgerService(db_session).deposit(user=user, goal_id=goal_id, amount=Decimal("10.00"))

    response = client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers(user))
    assert response.status_code == 409


def test_delete_empty_goal_succeeds(client, make_user, auth_headers):
    user = make_user()
    goal_id = _create_goal(client, auth_headers(user)).json()["id"]

    response = client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers(user))
    assert response.status_code == 204
