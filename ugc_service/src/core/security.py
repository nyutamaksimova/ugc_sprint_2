from uuid import UUID

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt


def decode_user_id(token: str, secret: str, algorithm: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"require_exp": True, "require_sub": True},
        )
        return UUID(payload["sub"])
    except (JWTError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from error


def current_user(credentials: HTTPAuthorizationCredentials, secret: str, algorithm: str) -> UUID:
    return decode_user_id(credentials.credentials, secret, algorithm)


bearer_scheme = HTTPBearer()
