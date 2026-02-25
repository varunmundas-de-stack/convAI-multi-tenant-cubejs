"""
Cube.js JWT token generator.

Flask generates a short-lived JWT (signed with CUBEJS_API_SECRET) that it
forwards to Cube.js on every query.  Cube.js validates it in checkAuth and
extracts the securityContext so it can:
  - Select the correct DuckDB schema  (clientId)
  - Apply row-level security          (role + hierarchy_code)
"""
import os
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT


def generate_cubejs_token(user) -> str:
    """
    Build a signed JWT for the given Flask-Login User object.

    Payload fields consumed by cubejs/cube.js:
      clientId       — maps to DuckDB schema  (client_nestle / client_unilever / client_itc)
      userId         — user identifier for audit purposes
      role           — SO / ASM / ZSM / NSM / admin / analyst
      hierarchy_code — the code to enforce in queryRewrite (so_code / asm_code / etc.)
      exp            — standard JWT expiry (8 hours)
    """
    secret = os.getenv('CUBEJS_API_SECRET')
    if not secret:
        raise RuntimeError('CUBEJS_API_SECRET environment variable is not set')

    # Pick the hierarchy code that matches the user's role level
    hierarchy_code = _pick_hierarchy_code(user)

    payload = {
        'clientId': user.client_id,
        'userId': user.id,
        'username': user.username,
        'role': user.role,
        'hierarchy_code': hierarchy_code,
        'exp': datetime.now(tz=timezone.utc) + timedelta(hours=8),
        'iat': datetime.now(tz=timezone.utc),
    }

    return jwt.encode(payload, secret, algorithm='HS256')


def _pick_hierarchy_code(user) -> str | None:
    """Return the most-specific hierarchy code for the user's role."""
    role = (user.role or '').upper()
    if role == 'SO' and user.so_code:
        return user.so_code
    if role == 'ASM' and user.asm_code:
        return user.asm_code
    if role == 'ZSM' and user.zsm_code:
        return user.zsm_code
    if role == 'NSM' and user.nsm_code:
        return user.nsm_code
    # Admin / analyst / national roles — no territory restriction
    return None
