from fastapi import APIRouter, HTTPException, status, Depends, Response
from datetime import datetime, timezone
from app.models.responses.account import AccountData
from app.models.requests.auth import AccountLoginRequest
from app.db.mongo import Mongo
from app.deps import get_mongo
from app.models.responses.auth import AccountLoginResponse
from app.util.hash import Hasher
from app.util.token import Tokenizer
from app.util.cookie import set_auth_cookies
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post(
    "/login",
    summary="Login to Account",
    description="Authenticate the account and return tokens"
)
async def login(
    req: AccountLoginRequest,
    response: Response,
    db: Mongo = Depends(get_mongo)
) -> AccountLoginResponse:
    try:
        account = await db.find_one("accounts", {"email": req.email.lower()})
        if not account:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not Hasher.verify(account["password"], req.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        id = str(account["_id"])
        access_token = Tokenizer.create_access_token(id)
        refresh_token = Tokenizer.create_refresh_token(id)
        
        set_auth_cookies(response, access_token, refresh_token)
        
        await db.update_one(
            "accounts",
            {"_id": account["_id"]},
            {"last_login": datetime.now(tz=timezone.utc)})
        
        return AccountLoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            data=AccountData(
                id=id,
                username=account["username"],
                email=account["email"],
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