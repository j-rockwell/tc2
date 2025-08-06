from pydantic import BaseModel

class SessionInviteRequest(BaseModel):
    account_id: str

class SessionInviteAcceptRequest(BaseModel):
    session_id: str