from pydantic import (
    BaseModel,
    EmailStr,
    Field,
)

class AccountCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str