import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from .database import get_db
from .database_models import UserDB


SECRET_KEY = os.getenv("TASKFLOW_SECRET_KEY", "")
if len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError(
        "TASKFLOW_SECRET_KEY must be set to a random value of at least 32 bytes. "
        "Configure it in .env and start Uvicorn with --env-file .env."
    )

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
password_hasher = PasswordHash.recommended()
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserDB:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication is required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
        if not isinstance(payload, dict):
            raise ValueError("Invalid token claims")
        subject = payload.get("sub")
        user_id = int(subject)
        if user_id < 1:
            raise ValueError("Invalid subject")
    except (InvalidTokenError, TypeError, ValueError):
        raise unauthorized

    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if user is None:
        raise unauthorized
    return user
