"""
Supabase HTTP client for Vercel Serverless.
Uses httpx to call the Supabase REST API directly,
avoiding supabase-py SDK issues with read-only filesystems.
"""
import os
import httpx

# Timeout for HTTP requests (seconds)
_TIMEOUT = 15.0


def _get_config():
    """Read Supabase config from environment variables at call time."""
    return {
        "url": os.environ.get("SUPABASE_URL", ""),
        "anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
        "service_role_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
    }


# ============================================
# Auth helpers (Supabase GoTrue REST API)
# ============================================

def admin_create_user(email: str, password: str, user_metadata: dict | None = None) -> dict:
    """
    Create a user via the Supabase Admin API.
    POST /auth/v1/admin/users
    Requires service_role_key.
    """
    cfg = _get_config()
    url = f"{cfg['url']}/auth/v1/admin/users"
    key = cfg["service_role_key"] or cfg["anon_key"]

    body = {
        "email": email,
        "password": password,
        "email_confirm": True,
    }
    if user_metadata:
        body["user_metadata"] = user_metadata

    resp = httpx.post(
        url,
        json=body,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        raise Exception(f"Supabase admin create_user failed ({resp.status_code}): {detail}")

    return resp.json()


def admin_delete_user(user_id: str) -> None:
    """
    Delete a user via the Supabase Admin API.
    DELETE /auth/v1/admin/users/:id
    """
    cfg = _get_config()
    key = cfg["service_role_key"] or cfg["anon_key"]
    url = f"{cfg['url']}/auth/v1/admin/users/{user_id}"

    resp = httpx.delete(
        url,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        raise Exception(f"Supabase admin delete_user failed ({resp.status_code}): {resp.text}")


def sign_in_with_password(email: str, password: str) -> dict:
    """
    Sign in via Supabase GoTrue.
    POST /auth/v1/token?grant_type=password
    """
    cfg = _get_config()
    url = f"{cfg['url']}/auth/v1/token?grant_type=password"

    resp = httpx.post(
        url,
        json={"email": email, "password": password},
        headers={
            "apikey": cfg["anon_key"],
            "Content-Type": "application/json",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        detail = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text
        raise Exception(f"Login failed ({resp.status_code}): {detail}")

    return resp.json()


def get_user_by_token(token: str) -> dict:
    """
    Verify JWT and retrieve the user.
    GET /auth/v1/user
    """
    cfg = _get_config()
    url = f"{cfg['url']}/auth/v1/user"

    resp = httpx.get(
        url,
        headers={
            "apikey": cfg["anon_key"],
            "Authorization": f"Bearer {token}",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        raise Exception(f"Token verification failed ({resp.status_code}): {resp.text}")

    return resp.json()


# ============================================
# PostgREST helpers (Database operations)
# ============================================

def db_select(table: str, columns: str = "*", filters: dict | None = None,
              order: str | None = None, desc: bool = True,
              limit: int | None = None, offset: int | None = None,
              token: str | None = None) -> list:
    """
    SELECT from a PostgREST table.
    GET /rest/v1/{table}?select={columns}&...
    """
    cfg = _get_config()
    url = f"{cfg['url']}/rest/v1/{table}"
    key = cfg["anon_key"]

    params = {"select": columns}
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {token or key}",
    }

    if filters:
        for col, val in filters.items():
            params[col] = f"eq.{val}"

    if order:
        params["order"] = f"{order}.{'desc' if desc else 'asc'}"

    if limit is not None:
        headers["Range"] = f"{offset or 0}-{(offset or 0) + limit - 1}"
        headers["Prefer"] = "count=exact"

    resp = httpx.get(url, params=params, headers=headers, timeout=_TIMEOUT)

    if resp.status_code >= 400:
        raise Exception(f"DB select failed ({resp.status_code}): {resp.text}")

    return resp.json()


def db_insert(table: str, data: dict, token: str | None = None) -> list:
    """
    INSERT into a PostgREST table.
    POST /rest/v1/{table}
    """
    cfg = _get_config()
    url = f"{cfg['url']}/rest/v1/{table}"
    key = cfg["anon_key"]

    resp = httpx.post(
        url,
        json=data,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {token or key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        raise Exception(f"DB insert failed ({resp.status_code}): {resp.text}")

    return resp.json()


def db_delete(table: str, filters: dict, token: str | None = None) -> None:
    """
    DELETE from a PostgREST table.
    DELETE /rest/v1/{table}?filters...
    """
    cfg = _get_config()
    url = f"{cfg['url']}/rest/v1/{table}"
    key = cfg["anon_key"]

    params = {}
    for col, val in filters.items():
        params[col] = f"eq.{val}"

    resp = httpx.delete(
        url,
        params=params,
        headers={
            "apikey": key,
            "Authorization": f"Bearer {token or key}",
        },
        timeout=_TIMEOUT,
    )

    if resp.status_code >= 400:
        raise Exception(f"DB delete failed ({resp.status_code}): {resp.text}")
