# SaveUp Database Schema

> **Implementation status note:** the shipped schema (see
> `backend/app/models/` and `backend/alembic/versions/`) follows this
> document closely but is not a 1:1 match. Differences, and why:
>
> - **`deposits` was merged into `transactions`.** Rather than two
>   overlapping money tables, all money movement (deposit, withdrawal,
>   refund) lives in one `transactions` ledger distinguished by
>   `transaction_type`, so there is exactly one place enforcing
>   idempotency, row-locking, and the no-negative-balance invariant.
> - **`refresh_tokens` was added** (not in this doc) to support JWT
>   refresh rotation with reuse-detection, one of the explicit auth
>   requirements.
> - **`payment_attempts` was added** alongside `payment_orders` to record
>   every webhook delivery/attempt against an order — needed to make the
>   webhook handler idempotent under duplicate delivery.
> - **`devices`, `goal_milestones`, `challenges`, `user_challenges`, and
>   `payment_methods` are not implemented** in this pass. Device/session
>   tracking is out of scope beyond refresh-token rotation; goal
>   milestones are handled as notification *events* rather than a
>   persisted table; challenges and saved payment methods are flagged as
>   future work in the root `README.md`.

Version: 1.0

---

# Database

PostgreSQL

Naming Convention

- snake_case
- UUID Primary Keys
- created_at
- updated_at

---

# 1. users

Purpose

Store user information.

Columns

id (UUID) PK

phone_number

name

email

profile_picture

date_of_birth

kyc_status

pan_number

is_active

created_at

updated_at

---

# 2. devices

Purpose

Track logged-in devices.

Columns

id

user_id FK

device_name

device_id

device_type

last_login

is_active

created_at

---

# 3. emergency_contacts

Purpose

Store emergency approval contacts.

Columns

id

user_id FK

contact_name

relationship

phone_number

is_verified

created_at

---

# 4. goals

Purpose

Store user saving goals.

Columns

id

user_id FK

title

category

goal_image

target_amount

saved_amount

monthly_target

deadline

lock_type

status

completed_at

created_at

updated_at

Status

ACTIVE

PAUSED

COMPLETED

ARCHIVED

Lock Types

EASY

MEDIUM

HARD

---

# 5. deposits

Purpose

Store successful deposits.

Columns

id

goal_id FK

user_id FK

amount

payment_method

payment_gateway

gateway_transaction_id

status

created_at

Status

SUCCESS

FAILED

PENDING

REFUNDED

---

# 6. withdrawal_requests

Purpose

Track emergency withdrawal requests.

Columns

id

goal_id FK

user_id FK

amount

reason

status

requested_at

approved_at

cooldown_end

completed_at

Status

PENDING

APPROVED

REJECTED

COOLDOWN

COMPLETED

CANCELLED

---

# 7. transactions

Purpose

Unified transaction history.

Columns

id

user_id FK

goal_id FK

transaction_type

reference_id

amount

status

created_at

Transaction Types

DEPOSIT

WITHDRAWAL

REFUND

Status

SUCCESS

FAILED

PENDING

---

# 8. notifications

Purpose

Store notifications.

Columns

id

user_id FK

title

message

type

is_read

created_at

Types

REMINDER

GOAL

PAYMENT

SYSTEM

ACHIEVEMENT

---

# 9. achievements

Purpose

Master achievement list.

Columns

id

title

description

badge_image

required_value

created_at

---

# 10. user_achievements

Purpose

Achievements unlocked by users.

Columns

id

user_id FK

achievement_id FK

unlocked_at

---

# 11. streaks

Purpose

Track user consistency.

Columns

id

user_id FK

current_streak

best_streak

last_saved_date

updated_at

---

# 12. goal_milestones

Purpose

Track milestone completion.

Columns

id

goal_id FK

milestone

completed

completed_at

Milestones

25

50

75

100

---

# 13. challenges

Purpose

Available saving challenges.

Columns

id

title

description

target

duration

reward

created_at

---

# 14. user_challenges

Purpose

User challenge participation.

Columns

id

user_id FK

challenge_id FK

progress

status

joined_at

completed_at

Status

ACTIVE

COMPLETED

FAILED

---

# 15. payment_methods

Purpose

Store saved payment methods.

Columns

id

user_id FK

type

provider

last_four_digits

is_default

created_at

---

# Relationships

User

↓

Goals

↓

Deposits

↓

Transactions

↓

Withdrawal Requests

--------------------------------

User

↓

Emergency Contact

--------------------------------

User

↓

Notifications

--------------------------------

User

↓

Achievements

--------------------------------

User

↓

Streak

--------------------------------

Goal

↓

Milestones

--------------------------------

Challenge

↓

User Challenges

---

# Indexes

users.phone_number

goals.user_id

deposits.user_id

transactions.user_id

withdrawal_requests.user_id

notifications.user_id

---

# Cascade Rules

Delete User

↓

Delete Goals

↓

Delete Deposits

↓

Delete Transactions

↓

Delete Notifications

---

# Estimated Tables

15

Estimated Columns

~130+

Estimated Relations

20+
