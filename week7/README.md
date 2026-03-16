# Week 7 – Shareable Links for Notes

This update adds public sharing functionality to the existing Flask Notes API.
Users can generate unique shareable links for notes, optionally set an expiration date, and track how many times the link has been accessed.

The Postman Collection for testing the feature is available in:
`api_tests.yaml`

---

## Overview

The following capabilities were added:

1. Generate unique shareable links for any note.
2. Optionally set an expiration date for the share link.
3. Public access to notes through the generated link.
4. Access count tracking for each shared link.

Share links are generated using a UUID token, which acts as a public identifier for accessing the note.

Example share link:

```
/share/{token}
```

---

## Setup

1. Clone the repository

2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate
```

3. Install dependencies

```
pip install -r requirements.txt
```

4. Create MySQL database

```
CREATE DATABASE notes_db;
```

5. Configure `.env`

```
MYSQL_USER=your_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=notes_db
SECRET_KEY=your_secret
JWT_SECRET_KEY=your_jwt_secret
```

6. Run the application

```
python app.py
```

---

## New API Endpoints

### Create Share Link 

Generates a public share link for a note.

```
POST /notes/<note_id>/share
```

Optional request body:

```json
{
  "expires_at": "2026-04-01T00:00:00"
}
```

Example response:

```json
{
  "token": "b58b7777-0177-4beb-a1f1-67a87eac42be",
  "expires_at": null,
  "access_count": 0
}
```

---

### Access Shared Note (Public)

Retrieves a note using its share token.

```
GET /share/<token>
```

Example response:

```json
{
  "category": "Work",
  "content": "Leg day",
  "created_at": "Mon, 16 Mar 2026 16:00:09 GMT",
  "id": 3,
  "tags": ["health"],
  "title": "Gym session",
  "updated_at": "Mon, 16 Mar 2026 16:00:09 GMT"
}
```

Each successful request increments the access_count associated with the share link.

---

# Share Link Behavior

* Share links are generated using UUID tokens.
* Tokens are unique and hard to guess.
* Links may optionally expire based on the `expires_at` value.
* Accessing a shared note increments the access counter stored in the database.
