from pydantic import BaseModel
from typing import List
from app.schema.exercise_session import ExerciseSession, ExerciseSessionParticipant, ExerciseSessionInDB

class SessionQueryResponse(BaseModel):
    data: List[ExerciseSessionInDB]

class SessionCreateResponse(BaseModel):
    session: ExerciseSession

class SessionInviteAcceptResponse(BaseModel):
    session: ExerciseSession
    participant: ExerciseSessionParticipant