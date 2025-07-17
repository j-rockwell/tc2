from fastapi import APIRouter, status, HTTPException, Response, Request, Depends
from fastapi.security import HTTPBearer
from app.deps import get_mongo, get_redis
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse, AccountData
from app.models.responses.base import ErrorResponse
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.config import settings
from app.util.cookie import set_auth_cookies
from app.util.session import Sessions, SessionSecurity, get_client_info
from datetime import datetime, timezone
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

async def get_account_kv():
    pass

async def get_account():
    pass

async def get_account_fuzzy():
    pass

async def get_account_availability():
    pass

async def get_profile():
    pass

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

async def update_account():
    pass

async def delete_account():
    pass