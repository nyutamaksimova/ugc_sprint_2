from functools import wraps
from typing import Callable, ParamSpec, TypeVar

import jwt
from flask import current_app, jsonify, request


P = ParamSpec("P")
R = TypeVar("R")


def require_user(view: Callable[..., R]) -> Callable[P, R]:
    @wraps(view)
    def wrapped(*args: P.args, **kwargs: P.kwargs):
        authorization = request.headers.get("Authorization", "")
        prefix, _, token = authorization.partition(" ")
        if prefix != "Bearer" or not token or " " in token:
            return _unauthorized()

        try:
            claims = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=[current_app.config["JWT_ALGORITHM"]],
            )
        except jwt.PyJWTError:
            return _unauthorized()

        user_id = claims.get("sub")
        if not isinstance(user_id, str) or not user_id:
            return _unauthorized()
        return view(user_id, *args, **kwargs)

    return wrapped


def _unauthorized():
    return jsonify(
        code="unauthorized", message="Valid bearer token is required"
    ), 401
