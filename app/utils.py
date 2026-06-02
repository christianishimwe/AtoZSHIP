from pathlib import Path
from itsdangerous import BadSignature, Serializer, SignatureExpired, URLSafeTimedSerializer
import jwt
from app.config import database_settings
from datetime import datetime, timedelta, timezone
from uuid import uuid4

_serializer = URLSafeTimedSerializer(database_settings.JWT_SECRET_KEY)

APP_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = APP_DIR.joinpath("templates")


def generate_access_token(
        data: dict,
        expiry: timedelta = timedelta(minutes=15)
) -> str | None:
    try:
        return jwt.encode(
            payload={
                **data,
                "jti": str(uuid4()),
                "exp": datetime.now(timezone.utc) + expiry,
            },
            algorithm=database_settings.JWT_ALGORITHM,
            key=database_settings.JWT_SECRET_KEY
        )
    except jwt.PyJWTError:
        return None


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            jwt=token,
            key=database_settings.JWT_SECRET_KEY,
            algorithms=[database_settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None


def generate_url_safe_token(data: dict, salt: str | None = None) -> str:
    # generate the token
    return _serializer.dumps(data, salt=salt)


def decode_url_safe_token(token: str, expiry: timedelta | None = None, salt: str | None = None):
    try:
        return _serializer.loads(
            token,
            max_age=int(expiry.total_seconds()) if expiry else None,
            salt=salt
        )
    except (BadSignature, SignatureExpired):
        return None
