"""
AgentOps — Security Utilities
================================

WHY JWT?
--------
JWT (JSON Web Token) is the standard for stateless authentication in APIs.

How it works:
1. User logs in with email + password
2. Server verifies password using bcrypt hash comparison
3. Server generates a JWT token signed with JWT_SECRET
4. Client stores token (localStorage or memory)
5. Client sends token in every request header: Authorization: Bearer <token>
6. Server verifies the token signature on every protected request

The token DOES NOT require a database lookup per request — it's self-contained.
This is why it's "stateless".

ABOUT PASSWORD HASHING:
-----------------------
Passwords are NEVER stored in plain text.
We use bcrypt which:
- Adds a random "salt" before hashing (prevents rainbow table attacks)
- Has a "work factor" (slow by design — makes brute force impractical)
- Produces a different hash every time even for the same password

NEVER compare passwords directly. Always use verify_password().
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Password Hashing ──────────────────────────────────────
# bcrypt 4.x changed its API and passlib 1.7.4 hasn't caught up.
# We use bcrypt directly for Python 3.14 / bcrypt 5.x compatibility.
import bcrypt as _bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Always call this before storing a password.
    Returns a hash like: $2b$12$...
    """
    salt = _bcrypt.gensalt(rounds=12)
    hashed = _bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a stored bcrypt hash.
    
    Returns True if the password matches, False otherwise.
    Safe to use in login flows.
    """
    try:
        return _bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


# ── JWT Token Management ──────────────────────────────────
def create_access_token(
    user_id: str,
    email: str,
    expires_in_hours: Optional[int] = None
) -> str:
    """
    Create a signed JWT access token.
    
    The token contains:
    - sub: user_id (the "subject" of the token)
    - email: user's email
    - exp: expiry timestamp
    - iat: issued at timestamp
    
    Args:
        user_id: UUID of the authenticated user
        email: User's email address
        expires_in_hours: Override default expiry (defaults to JWT_EXPIRY_HOURS)
    
    Returns:
        Signed JWT token string
    """
    expiry_hours = expires_in_hours or settings.JWT_EXPIRY_HOURS
    expire = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
    
    payload = {
        "sub": user_id,          # Standard JWT claim: subject
        "email": email,
        "exp": expire,           # Standard JWT claim: expiry
        "iat": datetime.now(timezone.utc),  # Issued at
        "type": "access",
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.info("token_created", user_id=user_id)
    return token


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT access token.
    
    Returns:
        Token payload dict if valid
        None if token is invalid, expired, or tampered
    
    This is called on every protected API request.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Verify required fields
        if payload.get("sub") is None:
            logger.warning("token_missing_subject")
            return None
            
        return payload
        
    except JWTError as e:
        logger.warning("token_invalid", error=str(e))
        return None
