from pydantic import BaseModel
from app.schema.session import ExerciseSession

class SessionCreateResponse(BaseModel):
    id: str

class SessionInviteAcceptResponse(BaseModel):
    session: ExerciseSession