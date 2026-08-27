from uuid import uuid4

import pytest
from fastapi import HTTPException
from jose import jwt

from src.core.security import decode_user_id


def test_decode_user_id_returns_token_subject():
    user_id = uuid4()
    token = jwt.encode({"sub": str(user_id)}, "test-secret", algorithm="HS256")

    assert decode_user_id(token, "test-secret", "HS256") == user_id


def test_decode_user_id_rejects_invalid_token():
    with pytest.raises(HTTPException) as error:
        decode_user_id("invalid", "test-secret", "HS256")

    assert error.value.status_code == 401
