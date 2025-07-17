from typing import List, Optional
from pydantic import BaseModel

class AccountData(BaseModel):
    id: str
    username: str
    email: str

class AccountCreateResponse(BaseModel):
    access_token: str
    refresh_token: str
    data: AccountData

class AccountAvailabilityResponse(BaseModel):
    result: bool

class AccountSearchEntry(BaseModel):
    id: str
    username: str
    name: Optional[str]
    avatar: Optional[str]

class AccountSearchResponse(BaseModel):
    results: List[AccountSearchEntry]
    total: int