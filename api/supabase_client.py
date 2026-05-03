"""
Supabase HTTP client for Vercel Serverless.
Uses Python's built-in urllib to avoid any third-party library issues
with Vercel's read-only filesystem and serverless constraints.
"""
import os
import json
import urllib.request
import urllib.error
import urllib.parse

# Timeout for HTTP requests (seconds)
_TIMEOUT = 15


def _get_config():
    """Read Supabase config from environment variables at call time."""
    return {
        "url": os.environ.get("SUPABASE_URL", ""),
        "anon_key": os.environ.get("SUPABASE_ANON_KEY", ""),
        "service_role_key": os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
    }


def _do_request(method: str, url: str, headers: dict, body: dict | None = None) -> dict | list | None:
    """
    Perform an HTTP request using urllib (standard library).
    Returns parsed JSON response or raises an Exception with details.
    """
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8")
            if raw:
                return json.loads(raw)
            return None
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(error_body)
        except Exception:
            detail = error_body
        raise Exception(f"HTTP {e.code}: {detail}")


# ============================================
# Auth helpers (Supabase GoTrue REST API)
# ============================================

def admin_create_user(email: str, password: str, user_metadata: dict | None = None) -> dict:
    """
    Create a user via the Supabase Admin API.
    POST /auth/v1/admin/users
    """
    cfg = _get_config()
    key = cfg["service_role_key"] or cfg["anon_key"]
    url = f"{cfg['url']}/auth/v1/admin/users"

    body = {
        "email": email,
        "password": password,
        "email_confirm": True,
    }
    if user_metadata:
        body["user_metadata"] = user_metadata

    result = _do_request("POST", url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }, body)

    return result


def admin_delete_user(user_id: str) -> None:
    """
    Delete a user via the Supabase Admin API.
    DELETE /auth/v1/admin/users/:id
    """
    cfg = _get_config()
    key = cfg["service_role_key"] or cfg["anon_key"]
    url = f"{cfg['url']}/auth/v1/admin/users/{user_id}"

    _do_request("DELETE", url, {
        "apikey": key,
        "Authorization": f"Bearer {key}",
    })


def sign_in_with_password(email: str, password: str) -> dict:
    """
    Sign in via Supabase GoTrue.
    POST /auth/v1/token?grant_type=password
    """
    cfg = _get_config()
    url = f"{cfg['url']}/auth/v1/token?grant_type=password"

    result = _do_request("POST", url, {
        "apikey": cfg["anon_key"],
        "Content-Type": "application/json",
    }, {"email": email, "password": password})

    return result


def get_user_by_token(token: str) -> dict:
    """
    Verify JWT and retrieve the user.
    GET /auth/v1/user
    """
    cfg = _get_config()
    url = f"{cfg['url']}/auth/v1/user"

    result = _do_request("GET", url, {
        "apikey": cfg["anon_key"],
        "Authorization": f"Bearer {token}",
    })

    return result


# ============================================
# PostgREST helpers (Database operations)
# ============================================

def db_select(table: str, columns: str = "*", filters: dict | None = None,
              order: str | None = None, desc: bool = True,
              limit: int | None = None, offset: int | None = None,
              token: str | None = None) -> list:
    """
    SELECT from a PostgREST table.
    """
    cfg = _get_config()
    key = cfg["anon_key"]

    params = {"select": columns}
    if filters:
        for col, val in filters.items():
            params[col] = f"eq.{val}"
    if order:
        params["order"] = f"{order}.{'desc' if desc else 'asc'}"

    qs = urllib.parse.urlencode(params)
    url = f"{cfg['url']}/rest/v1/{table}?{qs}"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {token or key}",
    }
    if limit is not None:
        headers["Range"] = f"{offset or 0}-{(offset or 0) + limit - 1}"
        headers["Prefer"] = "count=exact"

    result = _do_request("GET", url, headers)
    return result if isinstance(result, list) else []


def db_insert(table: str, data: dict, token: str | None = None) -> list:
    """
    INSERT into a PostgREST table.
    """
    cfg = _get_config()
    key = cfg["anon_key"]
    url = f"{cfg['url']}/rest/v1/{table}"

    result = _do_request("POST", url, {
        "apikey": key,
        "Authorization": f"Bearer {token or key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }, data)

    return result if isinstance(result, list) else []


def db_delete(table: str, filters: dict, token: str | None = None) -> None:
    """
    DELETE from a PostgREST table.
    """
    cfg = _get_config()
    key = cfg["anon_key"]

    params = {}
    for col, val in filters.items():
        params[col] = f"eq.{val}"

    qs = urllib.parse.urlencode(params)
    url = f"{cfg['url']}/rest/v1/{table}?{qs}"

    _do_request("DELETE", url, {
        "apikey": key,
        "Authorization": f"Bearer {token or key}",
    })
