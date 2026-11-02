import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

# Load environment configuration
load_dotenv(".env.local")
load_dotenv()

# Initialize password hashing using pwdlib with recommended Argon2 algorithm
password_hash = PasswordHash.recommended()

# Supported safe HMAC algorithms
ALLOWED_JWT_ALGORITHMS = {"HS256", "HS384", "HS512"}
DEFAULT_TOKEN_EXPIRE_MINUTES = 1440


def get_jwt_secret_key() -> str:
    """
    Retrieve JWT secret key from environment.
    Raises RuntimeError if not configured, ensuring tokens cannot be forged or signed with fallbacks.
    """
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret or not secret.strip():
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured in environment (.env or .env.local). "
            "Please configure a strong, random secret key before issuing or verifying tokens."
        )
    return secret.strip()


def get_jwt_algorithm() -> str:
    """
    Retrieve and validate JWT algorithm from environment.
    Guards against insecure algorithms such as 'none' or unapproved cipher suites.
    """
    alg = os.getenv("JWT_ALGORITHM", "HS256").strip().upper()
    if alg not in ALLOWED_JWT_ALGORITHMS:
        raise ValueError(
            f"Unsupported or insecure JWT algorithm: '{alg}'. "
            f"Allowed algorithms are: {', '.join(sorted(ALLOWED_JWT_ALGORITHMS))}"
        )
    return alg


def get_token_expire_minutes() -> int:
    """Retrieve token expiration duration in minutes from environment."""
    val = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
    if not val:
        return DEFAULT_TOKEN_EXPIRE_MINUTES
    try:
        minutes = int(val)
        if minutes <= 0:
            raise ValueError()
        return minutes
    except ValueError:
        raise ValueError(f"ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer, got '{val}'.")


# ---------------------------------------------------------------------------
# 1. PASSWORD HASHING AND VERIFICATION
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2 via pwdlib."""
    if not password:
        raise ValueError("Password cannot be empty.")
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    if not password or not hashed_password:
        return False
    try:
        return password_hash.verify(password, hashed_password)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 2. JWT TOKEN CREATION AND VALIDATION
# ---------------------------------------------------------------------------

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Claims dictionary to encode (typically includes 'sub' and 'email').
        expires_delta: Optional custom token expiration duration.

    Returns:
        Encoded JWT token string.
    """
    secret = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()

    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=get_token_expire_minutes())

    to_encode.update({
        "exp": expire,
        "iat": now,
    })

    return jwt.encode(to_encode, secret, algorithm=algorithm)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decode and validate a JWT access token.

    Returns:
        Decoded payload dictionary if valid, or None if expired/invalid.
    """
    secret = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
