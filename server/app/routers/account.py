from fastapi import APIRouter, status, HTTPException, Response, Depends
from fastapi.security import HTTPBearer
from app.deps import get_mongo
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse
from app.models.responses.base import ErrorResponse
from app.schema.account import AccountBase
from app.db.mongo import Mongo
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.config import settings
from app.util.cookie import set_auth_cookies
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
        409: {"model": ErrorResponse, "description": "Username or Email is already in use"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def create_account(
    req: AccountCreateRequest,
    response: Response,
    db: Mongo = Depends(get_mongo)
) -> AccountBase:
    try:
        if await db.find_one("accounts", {"email": req.email}):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This email address is already in use")
        
        if await db.find_one("accounts", {"username": req.username.lower()}):
            raise HTTPException(status.HTTP_409_CONFLICT, detail="This username is already in use")
        
        pwd = Hasher.make(req.password)
        
        doc = {
            "email": req.email.lower(),
            "username": req.username,
            "password": pwd,
            "metadata": {
                "email_confirmed": False
            }
        }
        
        inserted = await db.insert("accounts", doc)
        account_id = str(inserted)
        
        access_token = Tokenizer.create_access_token(account_id, settings.access_token_secret, settings.access_token_ttl_minutes)
        refresh_token = Tokenizer.create_refresh_token(account_id, settings.refresh_token_secret, settings.refresh_token_ttl_minutes)
        res = AccountCreateResponse(id=account_id, access_token=access_token, refresh_token=refresh_token)
        
        set_auth_cookies(response, access_token, refresh_token)
        
        return res
    except HTTPException:
        raise
    except Exception as e:
    
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

async def update_account():
    pass

async def delete_account():
    pass