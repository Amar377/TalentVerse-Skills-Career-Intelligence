"""Authentication utilities: token creation, password hashing, and user dependencies."""
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from backend.database import get_db, User

security = HTTPBearer(auto_error=False)
DEMO_EMAIL_PREFIX = "demo-session-"
DEMO_EMAIL_DOMAIN = "@demo.talentverse.ai"
_TEMPORARY_DEMO_EMAIL = re.compile(
    rf"{re.escape(DEMO_EMAIL_PREFIX)}[0-9a-f]{{32}}{re.escape(DEMO_EMAIL_DOMAIN)}"
)


def is_temporary_demo_user(user: User) -> bool:
    return bool(user.is_demo) and _TEMPORARY_DEMO_EMAIL.fullmatch(user.email) is not None


def hash_password(password: str) -> str:
    """Return a salted, versioned PBKDF2-SHA256 password hash."""
    iterations = 310_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, iterations, salt_hex, digest_hex = hashed_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(iterations)
        if not 100_000 <= rounds <= 2_000_000:
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        # Support hashes created by earlier releases until successful login upgrades them.
        legacy_salt = SECRET_KEY[:16].encode("utf-8")
        legacy_hash = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), legacy_salt, 100_000).hex()
        return hmac.compare_digest(legacy_hash, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            return None
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.is_demo and not is_temporary_demo_user(user):
            return None
        return user
    except jwt.PyJWTError:
        return None


def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Require a valid authenticated user; demo access uses the explicit /auth/demo flow."""
    if current_user:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
