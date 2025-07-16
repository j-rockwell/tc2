from pydantic import BaseModel, EmailStr, validator, Field
import re

class AccountCreateRequest(BaseModel):
    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v