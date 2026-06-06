from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import jwt
import uuid
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
COOKIE_NAME = "session_token"
COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def create_token(user_id: str, name: str):
    payload = {
        "user_id": user_id,
        "name": name,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None


def get_or_create_user_id(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if token:
        payload = decode_token(token)
        if payload and "user_id" in payload:
            return payload["user_id"]
    return str(uuid.uuid4())


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        user_id = get_or_create_user_id(request)
        request.state.user_id = user_id

        response = await call_next(request)

        if COOKIE_NAME not in request.cookies:
            existing = response.headers.getlist("set-cookie")
            if not any(COOKIE_NAME in c for c in existing):
                token = create_token(user_id, "Anonymous")
                response.set_cookie(
                    key=COOKIE_NAME,
                    value=token,
                    max_age=COOKIE_MAX_AGE,
                    httponly=True,
                )

        return response


def get_current_user_id(request: Request):
    return get_or_create_user_id(request)

