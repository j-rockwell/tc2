from pydantic import BaseModel

class AccountData(BaseModel):
    id: str
    username: str
    email: str

class AccountCreateResponse(BaseModel):
    access_token: str
    refresh_token: str
    data: AccountData