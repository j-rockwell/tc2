from fastapi import Response
from app.config import settings

def set_auth_cookies(res: Response, access_token: str, refresh_token: str):
    res.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/"
    )
    
    res.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/"
    )

def clear_auth_cookies(res: Response):
    res.delete_cookie("access_token", path="/")
    res.delete_cookie("refresh_token", path="/")

