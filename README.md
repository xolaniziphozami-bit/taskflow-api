# TaskFlow API

TaskFlow is a REST API for managing personal tasks. It uses FastAPI, SQLAlchemy, SQLite, JWT access tokens, and Argon2 password hashing. Each task is tied to its owner, and authenticated users can only view or change their own tasks.

## Features

- Register an account and log in to receive a signed JWT access token.
- Store passwords as Argon2 hashes.
- Create, list, retrieve, update, and delete tasks.
- Restrict every task operation to the authenticated owner.
- Validate request data and return consistent HTTP errors.
- Explore the API in Swagger UI at `/docs`.
- Preserve existing SQLite task rows when enabling account ownership.

## Technology

- Python
- FastAPI and Uvicorn
- SQLAlchemy ORM
- SQLite
- Pydantic
- PyJWT
- `pwdlib` with Argon2
- `python-dotenv` for local environment files

## Run locally

From the repository folder, create and activate a virtual environment and install dependencies:

```sh
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

Create a local environment file and generate a signing key:

```sh
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Put the generated value in `TASKFLOW_SECRET_KEY` in `.env`. The key must be at least 32 bytes. Keep `.env` private; it is excluded from Git. Changing the key invalidates existing tokens.

Start the API:

```sh
uvicorn app.main:app --reload --env-file .env
```

Open the interactive API docs at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Authentication flow

1. Call `POST /auth/register` with a username and password. Usernames are case-insensitive, 3–50 characters, and may contain letters, numbers, dots, underscores, and hyphens. Passwords must be 8–128 characters.
2. Call `POST /auth/login` with the same credentials. The response contains a bearer access token that expires after 30 minutes.
3. In Swagger UI, select **Authorize** and paste the token. Then use the `/tasks` endpoints.
4. Call `GET /auth/me` to retrieve the signed-in account.

Example registration and login bodies:

```json
{
  "username": "xolani",
  "password": "a-long-unique-password"
}
```

## API endpoints

| Method | Path | Access | Purpose |
| --- | --- | --- | --- |
| `POST` | `/auth/register` | Public | Create an account |
| `POST` | `/auth/login` | Public | Get a JWT access token |
| `GET` | `/auth/me` | Token required | Get the current account |
| `POST` | `/tasks` | Token required | Create a task for the current account |
| `GET` | `/tasks` | Token required | List the current account's tasks |
| `GET` | `/tasks/{task_id}` | Token required | Retrieve an owned task |
| `PUT` | `/tasks/{task_id}` | Token required | Update an owned task |
| `DELETE` | `/tasks/{task_id}` | Token required | Delete an owned task |

Tasks belonging to another account, or tasks that do not exist, return `404` so the API does not reveal whether another user's task ID is valid.

## Existing database records

On startup, TaskFlow creates the new `users` table and adds a nullable `user_id` column to an existing `tasks` table when needed. Existing task rows are preserved. Since those older rows have no known owner, they remain unassigned and are not returned to any account. New tasks are associated with the authenticated user.

By default, the database is `tasks.db` in the current working directory. Set `TASKFLOW_DATABASE_URL` to use another SQLAlchemy database URL. Use a persistent database location when deploying.

## Project structure

```text
taskflow-api/
├── app/
│   ├── auth.py             # Password hashing, JWT creation and validation
│   ├── database.py         # Engine and session dependency
│   ├── database_models.py  # User and task tables
│   ├── main.py             # API routes and safe schema migration
│   └── models.py           # Pydantic request/response schemas
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Security notes

- Keep `TASKFLOW_SECRET_KEY` private and use a different strong value in each environment.
- Use HTTPS when exposing the API outside localhost.
- Do not commit `.env`, virtual environments, or the local SQLite database.
- This learning project does not yet include password recovery, refresh tokens, or rate limiting.
