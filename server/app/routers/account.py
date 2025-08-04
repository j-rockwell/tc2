from bson import ObjectId
from fastapi import APIRouter, status, HTTPException, Response, Request, Query, Depends
from fastapi.security import HTTPBearer
from app.deps import get_mongo, get_redis, read_request_account_id, read_request_account_id_optional
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse, AccountData, AccountAvailabilityResponse, AccountSearchEntry, AccountSearchResponse
from app.models.responses.base import ErrorResponse
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.config import settings
from app.util.cookie import clear_auth_cookies, set_auth_cookies
from app.util.session import Sessions, SessionSecurity, get_client_info
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging
import re

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

@router.get(
    "/availability",
    summary="Check username or email availability",
    description="Check if a specific username or email is available for registration",
    responses={
        400: {"model": ErrorResponse, "description": "Must provide username or email"},
    }
)
async def get_account_availability(
    username: Optional[str] = Query(None, min_length=2, max_length=16),
    email: Optional[str] = Query(None),
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
) -> AccountAvailabilityResponse:
    if not username and not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either username or email"
        )
    
    if username and email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide only one field at a time"
        )
    
    try:
        if username:
            value = username.lower()
            cache_key = f"username_exists:{value}"
            db_query = {"username": value}
        else:
            value = email.lower()
            cache_key = f"email_exists:{value}"
            db_query = {"email": value}
        
        available = True
        
        if redis:
            cached = await redis.get(cache_key)
            if cached == "true":
                available = False
            elif cached != "false":
                exists = await db.find_one("accounts", db_query)
                if exists:
                    await redis.setex(cache_key, 300, "true")
                    available = False
                else:
                    await redis.setex(cache_key, 60, "false")
        else:
            exists = await db.find_one("accounts", db_query)
            if exists:
                available = False
        
        return AccountAvailabilityResponse(result=available)
    except Exception as e:
        logger.error(f"Failed to check availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.get(
    "/search",
    summary="Search accounts",
    description="Search for accounts by username (fuzzy search)"
)
async def get_account_fuzzy(
    q: str = Query(..., min_length=2, max_length=50),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: Optional[Dict[str, Any]] = Depends(read_request_account_id_optional),
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
):
    try:
        cache_key = f"search:{q.lower()}:{limit}"
        
        if redis:
            cached = await redis.get(cache_key, decode_json=True)
            if cached:
                return AccountSearchResponse(
                    results=[AccountSearchEntry(**item) for item in cached],
                    total=len(cached)
                )
        
        escaped_query = re.escape(q)
        regex_pattern = f".*{escaped_query}.*"
        
        search_filter = {
            "$or": [
                {"username": {"$regex": regex_pattern, "$options": "i"}},
                {"profile.name": {"$regex": regex_pattern, "$options": "i"}}
            ]
        }
        
        if current_user:
            search_filter["_id"] = {"$ne": ObjectId(current_user["id"])}
        
        accounts = await db.find_many(
            "accounts",
            search_filter,
            projection={"username": 1, "profile.name": 1, "profile.avatar": 1},
            limit=limit,
            sort=[("username", 1)]
        )
        
        results: List[AccountSearchEntry] = []
        for account in accounts:
            profile = account.get("profile", {})
            results.append(AccountSearchEntry(
                id=str(account["_id"]),
                username=account["username"],
                name=profile.get("name"),
                avatar=profile.get("avatar"),
            ))
        
        if redis:
            results_dict = [result.dict() for result in results]
            await redis.setex(cache_key, 300, results_dict)

        return AccountSearchResponse(
            results=results,
            total=len(results)
        )
    except Exception as e:
        logger.error(f"Failed to search accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.get(
    "/{identifier}",
    summary="Get account by ID or username",
    description="Retrieve account information by ID or username"
)
async def get_account(
    identifier: str,
    current_user: Optional[Dict[str, Any]] = Depends(read_request_account_id_optional),
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
):
    try:
        cache_key = f"account:{identifier.lower()}"
        
        if redis:
            cached = await redis.get(cache_key, decode_json=True)
            if cached:
                return cached
        
        query = {}
        try:
            if ObjectId.is_valid(identifier):
                query["_id"] = ObjectId(identifier)
            else:
                query["username"] = identifier.lower()
        except:
            query["username"] = identifier.lower()
        
        account = await db.find_one(
            "accounts",
            query,
            projection={
                "password": 0,
                "metadata.email_confirmed": 0
            }
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        profile = account.get("profile", {})
        bio = account.get("bio", {})
        privacy = account.get("privacy", {})
        
        is_own_profile = current_user and str(account["_id"]) == current_user["id"]
        
        profile_privacy = privacy.get("profile", "public")
        if profile_privacy == "private" and not is_own_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Profile is private"
            )
        
        result = {
            "id": str(account["_id"]),
            "username": account["username"],
            "email": account["email"] if is_own_profile else None,
            "profile": {
                "name": profile.get("name"),
                "avatar": profile.get("avatar")
            },
            "metadata": {
                "created_at": account.get("metadata", {}).get("created_at"),
                "last_active": account.get("metadata", {}).get("last_active")
            }
        }
        
        if is_own_profile or profile_privacy == "public":
            result["bio"] = {
                "dob": bio.get("dob") if is_own_profile else None,
                "gender": bio.get("gender"),
                "weight": bio.get("weight") if is_own_profile else None,
                "height": bio.get("height") if is_own_profile else None
            }
            result["privacy"] = privacy if is_own_profile else None
        
        if redis:
            await redis.setex(cache_key, 600, result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.get(
    "/me/profile",
    summary="Get current user profile",
    description="Get the authenticated user's complete profile"
)
async def get_profile(
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
):
    try:
        cache_key = f"profile:{current_user['id']}"
        
        if redis:
            cached = await redis.get(cache_key, decode_json=True)
            if cached:
                return cached
        
        account = await db.find_one(
            "accounts",
            {"_id": ObjectId(current_user["id"])},
            projection={"password": 0}
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        profile = account.get("profile", {})
        bio = account.get("bio", {})
        privacy = account.get("privacy", {})
        metadata = account.get("metadata", {})
        
        result = {
            "id": str(account["_id"]),
            "username": account["username"],
            "email": account["email"],
            "profile": {
                "name": profile.get("name"),
                "avatar": profile.get("avatar")
            },
            "bio": {
                "dob": bio.get("dob"),
                "gender": bio.get("gender"),
                "weight": bio.get("weight"),
                "height": bio.get("height")
            },
            "privacy": {
                "profile": privacy.get("profile", "public"),
                "messages": privacy.get("messages", "followers"),
                "comments": privacy.get("comments", "public")
            },
            "metadata": {
                "created_at": metadata.get("created_at"),
                "last_active": metadata.get("last_active"),
                "email_confirmed": metadata.get("email_confirmed", False)
            }
        }
        
        if redis:
            await redis.setex(cache_key, 300, result)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )



@router.post(
    "/",
    response_model=AccountCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse, "description": "Username or Email already in use"},
        422: {"model": ErrorResponse, "description": "Validation error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"}
    }
)
async def create_account(
    req: AccountCreateRequest,
    request: Request,
    response: Response,
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
) -> AccountCreateResponse:
    try:
        client_info = get_client_info(request)
        
        rate_key = f"register_rate:{req.email.lower()}"
        current_attempts = await redis.get(rate_key)
        
        if current_attempts and int(current_attempts) >= 5:
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many registration attempts")
        
        email_key = f"email_exists:{req.email.lower()}"
        username_key = f"username_exists:{req.username.lower()}"
        
        if await redis.get(email_key) == "true":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This email address is already in use")
        
        if await redis.get(username_key) == "true":
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This username is already in use")
        
        if await db.find_one("accounts", {"email": req.email.lower()}):
            await redis.setex(email_key, 3600, "true")
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This email address is already in use")
        
        if await db.find_one("accounts", {"username": req.username.lower()}):
            await redis.setex(username_key, 3600, "true")
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This username is already in use")
        
        await redis.setex(email_key, 300, "false")
        await redis.setex(username_key, 300, "false")
        
        pwd = Hasher.make(req.password)
        now = datetime.now(tz=timezone.utc)
        
        doc = {
            "email": req.email.lower(),
            "username": req.username,
            "password": pwd,
            "metadata": {
                "email_confirmed": False,
                "created_at": now,
                "last_active": now
            }
        }
        
        inserted = await db.insert("accounts", doc)
        account_id = str(inserted)
        
        access_token = Tokenizer.create_access_token(account_id)
        refresh_token = Tokenizer.create_refresh_token(account_id)
        
        await Sessions.create(
            redis, account_id, "access", req.username, req.email.lower(),
            client_info["ip"], client_info["user_agent"]
        )
        await Sessions.create(
            redis, account_id, "refresh", req.username, req.email.lower(),
            client_info["ip"], client_info["user_agent"]
        )
        
        user_data = {
            "id": account_id,
            "username": req.username,
            "email": req.email.lower(),
            "email_confirmed": False
        }
        await redis.setex(f"user:{account_id}", 3600, user_data)
        
        await redis.incr(rate_key)
        await redis.expire(rate_key, 3600)
        
        await redis.delete(email_key, username_key)
        await redis.setex(f"email_exists:{req.email.lower()}", 3600, "true")
        await redis.setex(f"username_exists:{req.username.lower()}", 3600, "true")
        
        await SessionSecurity.add_trusted_ip(redis, account_id, client_info["ip"])
        
        await SessionSecurity.log_event(
            redis, account_id, "account_created", 
            {"ip": client_info["ip"], "user_agent": client_info["user_agent"]},
            client_info["ip"]
        )
        
        res = AccountCreateResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            data=AccountData(
                id=account_id,
                username=req.username,
                email=req.email.lower()
            )
        )
        
        set_auth_cookies(response, access_token, refresh_token)
        
        logger.info(f"Account created successfully for user: {req.username}")
        return res
        
    except HTTPException:
        if 'rate_key' in locals():
            await redis.incr(rate_key)
            await redis.expire(rate_key, 3600)
        raise
    except Exception as e:
        logger.error(f"Failed to create account: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")



@router.delete(
    "/",
    summary="Delete account",
    description="Permanently delete the authenticated user's account"
)
async def delete_account(
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    response: Response = None,
    db: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
):
    try:
        account_id = current_user["id"]
        
        result = await db.delete_one("accounts", {"_id": ObjectId(account_id)})
        
        if result == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        if redis:
            await Sessions.invalidate_all(redis, account_id)
            
            await redis.delete(f"user:{account_id}")
            await redis.delete(f"profile:{account_id}")
            await redis.delete(f"account:{current_user['username'].lower()}")
            await redis.delete(f"account:{account_id}")
            await redis.delete(f"email_exists:{current_user['email'].lower()}")
            await redis.delete(f"username_exists:{current_user['username'].lower()}")
        
        clear_auth_cookies(response)
        
        logger.info(f"Account deleted for user: {current_user['username']}")
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )