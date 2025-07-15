from typing import Optional, Literal
from pydantic import BaseModel

class AuthEntry(BaseModel):
    provider: Literal["google", "apple"]
    provider_user_id: str
    email: Optional[str]