from fastapi import APIRouter, BackgroundTasks, status, HTTPException, Response, Depends
from app.deps import get_mongo
from app.models.requests.account import AccountCreateRequest
from app.models.responses.account import AccountCreateResponse
from app.schema.account import AccountBase, AccountInDB
from app.db.mongo import Mongo
from app.util.hash import make_hash
from app.util.token import make_token

router = APIRouter()

@router.post("/", response_model=AccountCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_account(req: AccountCreateRequest, response: Response, db: Mongo = Depends(get_mongo),) -> AccountBase:
    if await db.find_one("accounts", {"email": req.email}):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="This email address is already in use")
    
    if await db.find_one("accounts", {"username": req.username.lower()}):
        raise HTTPException(status.HTTP_409_CONFLICT, detail="This username is already in use")
    
    pwd = make_hash(req.password)
    
    doc = {
        "email": req.email.lower(),
        "username": req.username,
        "password": pwd,
    }
    
    inserted = await db.insert("accounts", doc)
    account_id = str(inserted)
    
    access_token = make_token(account_id, "passkey", 300) # TODO: Use config value
    refresh_token = make_token(account_id, "passkey", 1600) # TODO: Use config value
    res = AccountCreateResponse(id=account_id, access_token=access_token, refresh_token=refresh_token)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=300,
        expires=300,
        path="/"
    )
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=1600,
        expires=1600,
        path="/"
    )
    
    return res