from pydantic import BaseModel

class AccountCreateResponse(BaseModel):
    id: str
    access_token: str
    refresh_token: str