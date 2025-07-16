from fastapi import Response
from app.config import settings

def set_auth_cookies(res: Response, access_token: str, refresh_token: str):
    res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_prod(),
        samesite="lax",
        max_age=settings.access_token_ttl_minutes,
        path="/"
    )
    
    res.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_prod(),
        samesite="lax",
        max_age=settings.refresh_token_ttl_minutes,
        path="/"
    )

def clear_auth_cookies(res: Response):
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")

