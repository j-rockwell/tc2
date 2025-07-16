from fastapi import APIRouter, BackgroundTasks, status, HTTPException, Response, Depends
from app.deps import get_mongo
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse
from app.models.responses.base import ErrorResponse
from app.schema.account import AccountBase
from app.db.mongo import Mongo
from app.util.hash import make_hash
from app.util.token import make_token
from app.config import settings

router = APIRouter()

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
    if await db.find_one("accounts", {"email": req.email}):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="This email address is already in use")
    
    if await db.find_one("accounts", {"username": req.username.lower()}):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="This username is already in use")
    
    pwd = make_hash(req.password)
    
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
    
    access_token = make_token(account_id, settings.access_token_secret, settings.access_token_ttl_minutes)
    refresh_token = make_token(account_id, settings.refresh_token_secret, settings.refresh_token_ttl_minutes)
    res = AccountCreateResponse(id=account_id, access_token=access_token, refresh_token=refresh_token)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.is_prod(),
        samesite="lax",
        max_age=settings.access_token_ttl_minutes,
        expires=settings.access_token_ttl_minutes,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.is_prod(),
        samesite="lax",
        max_age=settings.refresh_token_ttl_minutes,
        expires=settings.refresh_token_ttl_minutes,
        path="/"
    )
    
    return res