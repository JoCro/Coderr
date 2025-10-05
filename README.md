# 📋 Coderr — Marketplace API (Django + DRF)

> Token-authenticated backend for **profiles**, **offers**, **orders**, and **reviews**.  
> Built with 🐍 **Django** & ⚙️ **Django REST Framework**.

---

## 🧭 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Quickstart](#-quickstart)
- [Authentication](#-authentication)
- [API at a Glance](#-api-at-a-glance)
- [Permissions & Rules](#-permissions--rules)
- [Data Model (simplified)](#-data-model-simplified)
- [Environment & Settings](#-environment--settings)
- [Media & File Uploads](#-media--file-uploads)
- [License](#-license)

---

## ✨ Features

- 🔐 **Auth**
  - `POST /api/registration/` — create user (type: `customer` | `business`) → returns Token
  - `POST /api/login/` — username + password → returns Token
- 👤 **Profiles**
  - `GET|PATCH /api/profile/{pk}/` — own profile read/update
  - `GET /api/profiles/business/` — all business profiles
  - `GET /api/profiles/customer/` — all customer profiles
- 🛍 **Offers**
  - `GET /api/offers/` — list with filters, search & ordering
  - `POST /api/offers/` — create (business only, ≥ 3 details)
  - `GET|PATCH|DELETE /api/offers/{id}/` — detail/update/delete
  - `GET /api/offerdetails/{id}/` — single detail
- 📦 **Orders**
  - `GET /api/orders/` — list related to current user
  - `POST /api/orders/` — create (customer only)
  - `PATCH /api/orders/{id}/` — update status (business only)
  - `DELETE /api/orders/{id}/` — delete (staff only)
  - `GET /api/order-count/{business_user_id}/` — in-progress count
  - `GET /api/completed-order-count/{business_user_id}/` — completed count
- ⭐ **Reviews**
  - `GET /api/reviews/` — list with filters (ordering: rating or updated_at)
  - `POST /api/reviews/` — create (customer only, one per business)
  - `PATCH|DELETE /api/reviews/{id}/` — edit/delete (reviewer only)
- ℹ️ **Base Info**
  - `GET /api/base-info/` — platform stats (review count, avg rating, etc.)

---

## 🛠 Tech Stack

- Python 3.13+
- Django 5.x
- Django REST Framework 3.15+
- DRF Token Auth
- django-cors-headers
- Pillow (image handling)
- filetype (Base64 detection)
- SQLite (default)

---

## ⚡ Quickstart

```bash
git clone https://github.com/JoCro/Coderr.git
cd Coderr-Projekt

python3 -m venv env
source env/bin/activate   # Windows: env\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🔑 Authentication

Token authentication is required for most endpoints.

**Register**

```http
POST /api/registration/
{
  "username": "example",
  "email": "example@mail.com",
  "password": "StrongPass123",
  "repeated_password": "StrongPass123",
  "type": "customer"
}
```

**Login**

```http
POST /api/login/
{ "username": "example", "password": "StrongPass123" }
```

Header for authenticated requests:

```
Authorization: Token <token>
```

---

## 🔎 API at a Glance

| Endpoint             | Method     | Description             | Permissions     |
| -------------------- | ---------- | ----------------------- | --------------- |
| `/api/profile/{id}/` | GET, PATCH | Retrieve/update profile | Owner only      |
| `/api/offers/`       | GET, POST  | List or create offers   | Auth / Business |
| `/api/orders/`       | GET, POST  | List or create orders   | Auth            |
| `/api/reviews/`      | GET, POST  | List or create reviews  | Auth            |
| `/api/base-info/`    | GET        | Stats overview          | Public          |

---

## 🛡 Permissions & Rules

- Public: registration, login, base-info
- Authenticated: profile access, offer listings
- Business users: create/edit offers, update order status
- Customers: create orders, post reviews
- Staff: delete orders

---

## 🧱 Data Model (simplified)

```
User ───┐
        │ 1:1
Profile ┘ → user_type, file, info

Offer → OfferDetail[*]
Order(customer,business)
Review(business_user, reviewer)
```

---

## ⚙️ Environment & Settings

Example Django settings additions:

```python
INSTALLED_APPS = [
    ...,
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "coderr_app",
    "user_auth_app",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    ...,
]

CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5500"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```

---

## 📷 Media & File Uploads

- Images via multipart or Base64
- Profile: `/api/profile/{id}/` (PATCH)
- Offers: `/api/offers/` (POST)
- Stored under `/media/profiles/` or `/media/offers/`

---

## 📄 License

MIT License
