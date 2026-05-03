"""
JWT authentication middleware for FastAPI.
Extracts and verifies the Supabase JWT from the Authorization header.
"""
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase_client import get_user_by_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify JWT token via Supabase and return user info.
    Injects user data into route handlers via Depends().
    """
    token = credentials.credentials

    try:
        user = get_user_by_token(token)

        if not user or not user.get("id"):
            raise HTTPException(status_code=401, detail="无效的认证令牌")

        email = user.get("email", "")
        metadata = user.get("user_metadata", {})
        username = metadata.get("username", email.split("@")[0] if email else "unknown")

        return {
            "id": user["id"],
            "email": email,
            "username": username,
            "token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"认证失败: {str(e)}")
