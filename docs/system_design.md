# SaveUp System Design
Version: 1.0

> **Implementation status note (added when the backend MVP was built):**
> This document is the pre-implementation design reference. The actual
> backend follows it closely, with a handful of concrete decisions made
> where this doc was silent or where the MVP scope was intentionally
> narrowed (EASY-lock goals bypassing the emergency-withdrawal workflow,
> challenges left as a placeholder, no background scheduler, etc.). See
> the root `README.md`'s "Design decisions worth knowing" and "Known
> limitations" sections for the authoritative, up-to-date list rather
> than inferring implementation details from this doc alone.

---

# 1. Overview

SaveUp is a goal-based savings platform that enables users to save money towards specific financial goals while preventing impulsive spending through a secure money-locking mechanism.

The application follows a Client-Server Architecture.

---

# 2. High Level Architecture

                    Flutter Mobile App
                           │
                     HTTPS REST API
                           │
                    FastAPI Backend
                           │
     ┌───────────────┬──────────────┬──────────────┐
     │               │              │              │
 PostgreSQL        Redis       Firebase OTP    Razorpay
     │               │
     │               │
     └───────────────┴──────────────┐
                                    │
                                   AWS S3
                                    │
                              Notification Service
                                    │
                                   FCM

---

# 3. Components

## Flutter

Responsibilities

- UI
- User Interaction
- Local Storage
- Calling APIs
- Showing Notifications

---

## FastAPI

Responsibilities

- Authentication
- Business Logic
- Goal Management
- Payment Processing
- Emergency Withdrawals
- Notification Scheduling

---

## PostgreSQL

Stores

- Users
- Goals
- Transactions
- Notifications
- Emergency Contacts
- Withdraw Requests
- Achievements
- Streaks

---

## Redis

Purpose

- OTP Cache
- Session Cache
- Rate Limiting
- Frequently Used Data

---

## Firebase Authentication

Purpose

- Mobile Number OTP Login

---

## Razorpay

Purpose

- Receive Deposits

---

## Firebase Cloud Messaging

Purpose

- Push Notifications

---

## AWS S3

Purpose

- Profile Pictures
- Goal Images

---

# 4. Authentication Flow

User

↓

Enter Phone Number

↓

OTP Generated

↓

Firebase Verifies OTP

↓

Backend Creates User

↓

JWT Token Generated

↓

Flutter Stores Token Securely

↓

User Logged In

---

# 5. Goal Creation Flow

User

↓

Create Goal

↓

Flutter Sends Request

↓

FastAPI Validates Data

↓

Goal Stored in PostgreSQL

↓

Success Response

↓

Dashboard Updated

---

# 6. Deposit Flow

User

↓

Select Goal

↓

Enter Amount

↓

Razorpay Payment

↓

Payment Success

↓

Backend Verification

↓

Transaction Stored

↓

Goal Amount Updated

↓

Notification Sent

---

# 7. Emergency Withdrawal Flow

User

↓

Select Goal

↓

Emergency Withdraw

↓

Reason Selection

↓

OTP to Emergency Contact

↓

Approval

↓

Cooling Period Starts

↓

Money Released

↓

Goal Updated

↓

Transaction Stored

---

# 8. Notification Flow

Scheduled Reminder

↓

Backend

↓

Firebase Cloud Messaging

↓

Flutter Receives Notification

↓

Display to User

---

# 9. Data Flow

Flutter

↓

HTTPS Request

↓

FastAPI

↓

Business Logic

↓

PostgreSQL

↓

Response

↓

Flutter UI Updated

---

# 10. Security

Authentication

- OTP Login
- JWT Authentication

Authorization

- Token Validation
- User Ownership Validation

Encryption

- HTTPS
- Passwordless Authentication

Payments

- Razorpay Signature Verification

---

# 11. Error Handling

Examples

- Invalid OTP
- Payment Failed
- Goal Not Found
- Unauthorized Access
- Invalid Amount

---

# 12. Scalability

Application should support

- 100+ Users (MVP)
- 10,000+ Users
- 100,000+ Users

Future scaling

Flutter

↓

Load Balancer

↓

Multiple FastAPI Servers

↓

Redis

↓

PostgreSQL Cluster

↓

Object Storage

---

# 13. Folder Structure

saveup/

docs/

backend/

frontend/

database/

assets/

---

# 14. Tech Stack

Frontend

Flutter

Backend

FastAPI

Database

PostgreSQL

Cache

Redis

Authentication

Firebase OTP

Payments

Razorpay

Notifications

Firebase Cloud Messaging

Storage

AWS S3

Deployment

Docker

Linux VPS

Nginx

---

# 15. Design Principles

- Modular Architecture
- RESTful APIs
- Stateless Backend
- Secure Authentication
- Scalable Database Design
- Mobile First
- Clean Code
- Separation of Concerns

---

# 16. Future Improvements

- Family Savings
- Group Goals
- Smart Analytics
- International Payments
- Web Dashboard