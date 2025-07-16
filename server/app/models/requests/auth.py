from pydantic import BaseModel, EmailStr

class AccountLoginRequest(BaseModel):
    email: EmailStr
    password: str