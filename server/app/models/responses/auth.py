from pydantic import BaseModel
from app.models.responses.account import AccountData

class AccountLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    data: AccountData

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int