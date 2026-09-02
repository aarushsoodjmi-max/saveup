# SaveUp API Documentation
Version: 1.0

> **Note:** the implemented backend follows this reference plus a few
> necessary additions this doc doesn't enumerate — refresh-token rotation
> (`POST /auth/refresh`), the full withdrawal state machine
> (`/resend-otp`, `/reject`, `/complete` alongside `/approve`/`/cancel`),
> `/payments/orders/{id}`, and the RBAC-protected `/admin/*` routes. See
> root `README.md` → "API overview" for the complete current list.

Base URL

/api/v1

Authentication

Bearer JWT Token

Content-Type

application/json

---

# AUTHENTICATION

## Send OTP

POST /auth/send-otp

Description

Send OTP to user's phone number.

Request

{
    "phone_number": "+919876543210"
}

Response

{
    "success": true,
    "message": "OTP Sent"
}

---

## Verify OTP

POST /auth/verify-otp

Request

{
    "phone_number": "+919876543210",
    "otp":"123456"
}

Response

{
    "success": true,
    "access_token":"JWT_TOKEN",
    "refresh_token":"REFRESH_TOKEN",
    "is_new_user":false
}

---

## Logout

POST /auth/logout

Authorization Required

Response

{
    "success":true
}

------------------------------------------------------------

# USER

## Get Profile

GET /users/me

Response

{
    "id":"",
    "name":"",
    "phone_number":"",
    "email":"",
    "profile_picture":"",
    "kyc_status":""
}

---

## Update Profile

PUT /users/me

Request

{
    "name":"",
    "email":"",
    "date_of_birth":""
}

------------------------------------------------------------

# GOALS

## Create Goal

POST /goals

Request

{
    "title":"MacBook Pro",
    "category":"Electronics",
    "target_amount":150000,
    "monthly_target":12000,
    "deadline":"2027-12-31",
    "lock_type":"MEDIUM"
}

Response

{
    "success":true,
    "goal_id":"UUID"
}

---

## Get All Goals

GET /goals

---

## Get Goal

GET /goals/{goal_id}

---

## Update Goal

PUT /goals/{goal_id}

---

## Delete Goal

DELETE /goals/{goal_id}

---

## Pause Goal

PATCH /goals/{goal_id}/pause

---

## Resume Goal

PATCH /goals/{goal_id}/resume

------------------------------------------------------------

# DEPOSITS

## Create Deposit Order

POST /payments/create-order

Request

{
    "goal_id":"",
    "amount":5000
}

Response

{
    "order_id":"",
    "amount":"",
    "currency":"INR"
}

---

## Verify Payment

POST /payments/verify

Request

{
    "order_id":"",
    "payment_id":"",
    "signature":""
}

------------------------------------------------------------

# TRANSACTIONS

## Get Transactions

GET /transactions

Query Parameters

?page=1

&limit=20

&type=deposit

&goal_id=

------------------------------------------------------------

# WITHDRAWALS

## Request Emergency Withdrawal

POST /withdrawals

Request

{
    "goal_id":"",
    "amount":5000,
    "reason":"Medical"
}

Response

{
    "request_id":"",
    "status":"PENDING_APPROVAL"
}

---

## Approve Withdrawal

POST /withdrawals/{id}/approve

Request

{
    "otp":"123456"
}

---

## Cancel Withdrawal

POST /withdrawals/{id}/cancel

------------------------------------------------------------

# NOTIFICATIONS

## Get Notifications

GET /notifications

---

## Mark Read

PATCH /notifications/{id}/read

------------------------------------------------------------

# STREAKS

## Get Current Streak

GET /streak

------------------------------------------------------------

# ACHIEVEMENTS

## Get Achievements

GET /achievements

------------------------------------------------------------

# CHALLENGES

## Get Challenges

GET /challenges

---

## Join Challenge

POST /challenges/{id}/join

------------------------------------------------------------

# DASHBOARD

## Dashboard

GET /dashboard

Response

{
    "total_saved":25000,
    "active_goals":4,
    "completed_goals":2,
    "current_streak":18,
    "monthly_saved":7500
}

------------------------------------------------------------

# SETTINGS

## Update Settings

PUT /settings

------------------------------------------------------------

# ADMIN

/admin/users

/admin/goals

/admin/reports

/admin/transactions

/admin/kyc

------------------------------------------------------------

Status Codes

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error