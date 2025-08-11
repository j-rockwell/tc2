from bson import ObjectId
from fastapi import APIRouter, status, HTTPException, Response, Request, Query, Depends
from fastapi.security import HTTPBearer
from app.deps import get_mongo, get_redis, read_request_account_id, read_request_account_id_optional
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse, AccountData, AccountAvailabilityResponse, AccountSearchEntry, AccountSearchResponse
from app.models.responses.base import ErrorResponse
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.repos.account import AccountRepository
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.util.cookie import clear_auth_cookies, set_auth_cookies
from app.util.session import Sessions, get_client_info
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
        elif email:
            value = email.lower()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must provide either username or email"
            )
        
        repo = AccountRepository(mongo=db, redis=redis)    
        available = True
        existing = await repo.get_account_by_key_value("username" if username else "email", value)
        if existing:
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
        escaped_query = re.escape(q)
        regex_pattern = f".*{escaped_query}.*"
        
        search_filter = {
            "$or": [
                {"username": {"$regex": regex_pattern, "$options": "i"}},
                {"profile.name": {"$regex": regex_pattern, "$options": "i"}}
            ]
        }
        
        if current_user:
            search_filter["_id"] = {"$ne": ObjectId(current_user["id"])} # type: ignore
        
        repo = AccountRepository(mongo=db, redis=redis)
        accounts = await repo.get_many_accounts_by_filter(
            filter=search_filter,
            projection={"username": 1, "profile.name": 1, "profile.avatar": 1},
            limit=limit,
            sort=[("username", 1)]
        )
        
        results: List[AccountSearchEntry] = []
        for account in accounts:
            if not account.profile:
                results.append(AccountSearchEntry(
                    id=str(account.id),
                    username=account.username,
                    name=None,
                    avatar=None
                ))
                continue
            
            results.append(AccountSearchEntry(
                id=str(account.id),
                username=account.username,
                name=account.profile.name if account.profile.name else None,
                avatar=account.profile.avatar if account.profile.avatar else None,
            ))

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
        query = {}
        try:
            if ObjectId.is_valid(identifier):
                query["_id"] = ObjectId(identifier)
            else:
                query["username"] = identifier.lower()
        except:
            query["username"] = identifier.lower()
        
        repo = AccountRepository(mongo=db, redis=redis)
        account = await repo.get_account_by_key_value("username" if "username" in query else "_id", identifier)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        profile = account.profile or None
        bio = account.bio or None
        privacy = account.privacy or None
        is_own_profile = current_user and account.id == current_user["id"]
        
        profile_privacy = privacy.profile if privacy else "public"
        if profile_privacy == "private" and not is_own_profile:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Profile is private"
            )
        
        result = {
            "id": account.id,
            "username": account.username,
            "email": account.email if is_own_profile else None,
            "profile": {
                "name": profile.name if profile else None,
                "avatar": profile.avatar if profile else None
            },
            "metadata": {
                "created_at": account.metadata.created_at if account.metadata else None,
                "last_active": account.metadata.last_active if account.metadata else None
            }
        }
        
        if is_own_profile or profile_privacy == "public":
            if bio and is_own_profile:
                result["bio"] = {
                    "dob": bio.dob if is_own_profile else None,
                    "gender": bio.gender if is_own_profile else None,
                    "weight": bio.weight if is_own_profile else None,
                    "height": bio.height if is_own_profile else None
                }
            
            if privacy and is_own_profile:
                result["privacy"] = {
                    "profile": privacy.profile if is_own_profile else None,
                    "messages": privacy.messages if is_own_profile else None,
                    "comments": privacy.comments if is_own_profile else None
                }
        
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
        repo = AccountRepository(mongo=db, redis=redis)
        created_account = await repo.create_account(username=req.username, email=req.email, password=req.password)
        if not created_account:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create account"
            )
        
        access_token = Tokenizer.create_access_token(created_account.id)
        refresh_token = Tokenizer.create_refresh_token(created_account.id)
        
        await Sessions.create(
            redis, created_account.id, "access", req.username, req.email.lower(),
            client_info["ip"], client_info["user_agent"]
        )
        
        res = AccountCreateResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            data=AccountData(
                id=created_account.id,
                username=req.username,
                email=req.email.lower()
            )
        )
        
        set_auth_cookies(response, access_token, refresh_token)
        
        logger.info(f"Account created successfully for user: {req.username}")
        return res
        
    except HTTPException:
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
    response: Response,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
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