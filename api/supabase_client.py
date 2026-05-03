"""
Supabase client initialization.
Provides both an admin client (service role) and a function to create
per-user clients using their JWT token.
"""
import os
from supabase import create_client, Client


def get_supabase_admin() -> Client:
    """
    Admin client using SERVICE_ROLE_KEY.
    Bypasses RLS - use only for admin operations (user management).
    """
    url = os.environ.get("SUPABASE_URL", "")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")

    if not service_key or service_key == "your_service_role_key_here":
        # Fallback to anon key if service role not configured
        return create_client(url, anon_key)
    return create_client(url, service_key)


def get_supabase_client() -> Client:
    """
    Standard client using ANON_KEY.
    Respects RLS policies. Used for most operations.
    """
    url = os.environ.get("SUPABASE_URL", "")
    anon_key = os.environ.get("SUPABASE_ANON_KEY", "")
    return create_client(url, anon_key)
