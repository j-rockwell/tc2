from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Response, Request, Cookie, Depends
from typing import Optional
from datetime import datetime, timezone
from app.models.responses.account import AccountData
from app.models.requests.auth import AccountLoginRequest, RefreshTokenRequest
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.util.session import Sessions, SessionSecurity, get_client_info
from app.deps import get_mongo, get_redis, read_request_account_id
from app.models.responses.auth import AccountLoginResponse, RefreshTokenResponse
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.util.cookie import set_auth_cookies, clear_auth_cookies
from app.config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/login",
    summary="Login to Account",
    description="Authenticate and create session",
    responses={
        401: {"description": "Invalid credentials"},
        423: {"description": "Account locked"},
        429: {"description": "Rate limit exceeded"},
        403: {"description": "Additional verification required"}
    }
)
async def login(
    req: AccountLoginRequest,
    request: Request,
    response: Response,
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
) -> AccountLoginResponse:
    try:
        client_info = get_client_info(request)
        
        rate_key = f"login_attempts:{req.email.lower()}"
        failed_key = f"failed_login:{req.email.lower()}"
        
        failed_attempts = await redis.get(failed_key)
        if failed_attempts and int(failed_attempts) >= 5:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account temporarily locked due to too many failed login attempts"
            )
        
        current_attempts = await redis.get(rate_key)
        if current_attempts and int(current_attempts) >= 10:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Please try again later"
            )
        
        user_cache_key = f"user_by_email:{req.email.lower()}"
        cached_user = await redis.get(user_cache_key, decode_json=True)
        
        account = None
        if cached_user:
            account = await db.find_one("accounts", {"_id": ObjectId(cached_user["_id"])})
            if not account:
                await redis.delete(user_cache_key)
                cached_user = None
        
        if not cached_user:
            account = await db.find_one("accounts", {"email": req.email.lower()})
            if account:
                cache_data = {
                    "_id": str(account["_id"]),
                    "email": account["email"],
                    "username": account["username"],
                    "password": account["password"],
                    "metadata": account.get("metadata", {})
                }
                await redis.setex(user_cache_key, 1800, cache_data)
        else:
            account = {
                "_id": ObjectId(cached_user["_id"]),
                "email": cached_user["email"],
                "username": cached_user["username"],
                "password": cached_user["password"],
                "metadata": cached_user.get("metadata", {})
            }
        
        if not account:
            await redis.incr(rate_key)
            await redis.expire(rate_key, 3600)
            await redis.incr(failed_key)
            await redis.expire(failed_key, 1800)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not Hasher.verify(account["password"], req.password):
            await redis.incr(rate_key)
            await redis.expire(rate_key, 3600)
            await redis.incr(failed_key)
            await redis.expire(failed_key, 1800)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        await redis.delete(failed_key)
        
        account_id = str(account["_id"])
        should_challenge = await SessionSecurity.should_challenge(
            redis, account_id, client_info["ip"], client_info["user_agent"]
        )
        
        if should_challenge:
            await SessionSecurity.log_event(
                redis, account_id, "suspicious_login",
                {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
                client_info["ip"]
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Additional verification required",
                headers={"X-Challenge-Required": "true"}
            )
        
        await redis.incr(rate_key)
        await redis.expire(rate_key, 3600)
        
        access_token = Tokenizer.create_access_token(account_id)
        refresh_token = Tokenizer.create_refresh_token(account_id)
        
        now = datetime.now(tz=timezone.utc)
        await db.update_one(
            "accounts",
            {"_id": account["_id"]},
            {"metadata.last_login": now, "metadata.last_active": now}
        )
        
        await Sessions.create(
            redis, account_id, "access", account["username"], account["email"],
            client_info["ip"], client_info["user_agent"]
        )
        await Sessions.create(
            redis, account_id, "refresh", account["username"], account["email"],
            client_info["ip"], client_info["user_agent"]
        )
        
        user_data = {
            "id": account_id,
            "username": account["username"],
            "email": account["email"],
            "email_confirmed": account.get("metadata", {}).get("email_confirmed", False),
            "last_login": now.isoformat()
        }
        await redis.setex(f"user:{account_id}", 3600, user_data)
        
        await SessionSecurity.add_trusted_ip(redis, account_id, client_info["ip"])
        
        await SessionSecurity.log_event(
            redis, account_id, "login_success",
            {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
            client_info["ip"]
        )
        
        set_auth_cookies(response, access_token, refresh_token)
        
        logger.info(f"Successful login for user: {account['username']}")
        
        return AccountLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            data=AccountData(
                id=account_id,
                username=account["username"],
                email=account["email"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to perform login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.post(
    "/logout",
    summary="Logout from current session",
    description="Invalidate current session and clear tokens"
)
async def logout(
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
    current_user: dict = Depends(read_request_account_id)
):
    try:
        account_id = current_user["id"]
        client_info = get_client_info(request)
        
        await Sessions.invalidate_all(redis, account_id)
        
        await SessionSecurity.log_event(
            redis, account_id, "logout",
            {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
            client_info["ip"]
        )
        
        clear_auth_cookies(response)
        
        logger.info(f"User logged out: {current_user['username']}")
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Failed to logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Generate a new access token using refresh token"
)
async def refresh_token(
    req: RefreshTokenRequest,
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
):
    try:
        payload = Tokenizer.decode_refresh_token(req.refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        account_id = payload.get("sub")
        if not account_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        if not await Sessions.is_valid(redis, account_id, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session expired or invalid"
            )
        
        client_info = get_client_info(request)
        
        security_check = await SessionSecurity.detect_suspicious(
            redis, account_id, client_info["ip"], client_info["user_agent"]
        )
        
        if security_check["score"] > 70:
            await SessionSecurity.log_event(
                redis, account_id, "high_suspicion_refresh",
                security_check, client_info["ip"]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Additional verification required",
                headers={"X-Challenge-Required": "true"}
            )
        
        new_access_token = Tokenizer.create_access_token(account_id)
        new_refresh_token = Tokenizer.create_refresh_token(account_id)
        
        session_data = await Sessions.get(redis, account_id, "refresh")
        if session_data:
            await Sessions.create(
                redis, account_id, "access", 
                session_data["username"], session_data["email"],
                client_info["ip"], client_info["user_agent"]
            )
            
            await Sessions.invalidate(redis, account_id, "refresh")
            await Sessions.create(
                redis, account_id, "refresh",
                session_data["username"], session_data["email"],
                client_info["ip"], client_info["user_agent"]
            )
        
        await Sessions.update(redis, account_id, "access", client_info["ip"])
        
        await SessionSecurity.log_event(
            redis, account_id, "token_refresh_success",
            {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
            client_info["ip"]
        )
        
        set_auth_cookies(response, new_access_token, new_refresh_token)
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_ttl_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.post(
    "/refresh-cookie",
    summary="Refresh access token",
    description="Generate new access token using refresh token"
)
async def refresh_token(
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
    refresh_token: Optional[str] = Cookie(None)
):
    try:
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required"
            )
        
        payload = Tokenizer.decode_refresh_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        account_id = payload.get("sub")
        if not account_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        if not await Sessions.is_valid(redis, account_id, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh session expired or invalid"
            )
        
        client_info = get_client_info(request)
        
        security_check = await SessionSecurity.detect_suspicious(
            redis, account_id, client_info["ip"], client_info["user_agent"]
        )
        
        if security_check["score"] > 70:
            await SessionSecurity.log_event(
                redis, account_id, "high_suspicion_refresh",
                security_check, client_info["ip"]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Additional verification required",
                headers={"X-Challenge-Required": "true"}
            )
        
        new_access_token = Tokenizer.create_access_token(account_id)
        new_refresh_token = Tokenizer.create_refresh_token(account_id)
        
        session_data = await Sessions.get(redis, account_id, "refresh")
        if session_data:
            await Sessions.create(
                redis, account_id, "access", 
                session_data["username"], session_data["email"],
                client_info["ip"], client_info["user_agent"]
            )
            
            await Sessions.invalidate(redis, account_id, "refresh")
            await Sessions.create(
                redis, account_id, "refresh",
                session_data["username"], session_data["email"],
                client_info["ip"], client_info["user_agent"]
            )
        
        await Sessions.update(redis, account_id, "access", client_info["ip"])
        
        await SessionSecurity.log_event(
            redis, account_id, "token_refresh_success",
            {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
            client_info["ip"]
        )
        
        set_auth_cookies(response, new_access_token, new_refresh_token)
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.access_token_ttl_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )