from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime, timezone
import json
import logging

from app.db.redis import Redis
from app.db.mongo import Mongo
from app.schema.exercise_session import ExerciseSessionInDB, ExerciseSessionState, ExerciseSessionStatus, ExerciseSession, ExerciseSessionParticipant, ExerciseSessionInvitation

collection_name = "exercise_sessions"
state_key = "exercise_session_state"

logger = logging.getLogger(__name__)

def build_state_key(session_id: str, account_id: str) -> str:
    return f"{state_key}:{session_id}:{account_id}"

class ExerciseSessionRepository:
    def __init__(self, mongo: Mongo, redis: Redis):
        self.mongo = mongo
        self.redis = redis

    async def get_session_by_id(self, session_id: str) -> Optional[ExerciseSessionInDB]:
        doc = await self.mongo.find_one_by_id(collection=collection_name, document_id=session_id)
        return ExerciseSessionInDB(**doc) if doc else None

    async def get_sessions_by_user(
        self,
        account_id: str,
        projection: Optional[Dict[str, Any]] = None,
        sort: Optional[List[Tuple[str, Union[int, str]]]] = None,
        skip: int = 0,
        limit: int = 0,
    ) -> List[ExerciseSessionInDB]:
        query = {"$or": [{"owner_id": account_id}, {"participants.id": account_id}]}
        docs = await self.mongo.find_many(
            collection=collection_name,
            filter_dict=query,
            projection=projection,
            sort=sort,
            skip=skip,
            limit=limit,
        )
        return [ExerciseSessionInDB(**s) for s in (docs or [])]

    async def get_active_session_by_user(self, account_id: str) -> Optional[ExerciseSessionInDB]:
        query = {
            "status": ExerciseSessionStatus.ACTIVE.value,
            "$or": [{"owner_id": account_id}, {"participants.id": account_id}],
        }
        doc = await self.mongo.find_one(collection=collection_name, filter_dict=query)
        return ExerciseSessionInDB(**doc) if doc else None

    async def get_session_state_by_session(self, session_id: str) -> List[ExerciseSessionState]:
        doc = await self.mongo.find_one(collection=collection_name, filter_dict={"_id": session_id})
        if not doc:
            return []

        session = ExerciseSessionInDB(**doc)
        if not session.participants:
            return []

        states: List[ExerciseSessionState] = []
        for p in session.participants:
            key = build_state_key(session.id, p.id)
            raw = await self.redis.get(key)
            if not raw:
                continue

            try:
                s = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
                data = json.loads(s)
                state = ExerciseSessionState.parse_obj(data)
                sid = getattr(state, "session_id", None)
                if sid and str(sid) != str(session_id):
                    logger.debug(
                        "Skipping state for %s: mismatched session_id (%s != %s)",
                        p.id, sid, session_id
                    )
                    continue
                states.append(state)
            except json.JSONDecodeError as e:
                logger.warning("Bad JSON for participant %s (key=%s): %s", p.id, key, e)
            except Exception as e:
                logger.warning("Bad state for participant %s (key=%s): %s", p.id, key, e)

        return states

    async def get_active_session_state_by_user(self, account_id: str) -> Optional[ExerciseSessionState]:
        session = await self.get_active_session_by_user(account_id)
        if not session:
            return None

        key = build_state_key(session.id, account_id)
        raw = await self.redis.get(key)
        if not raw:
            return None

        try:
            s = raw.decode("utf-8") if isinstance(raw, (bytes, bytearray)) else raw
            data = json.loads(s)
            state = ExerciseSessionState.parse_obj(data)
            return state if getattr(state, "session_id", None) in (None, str(session.id)) else None
        except json.JSONDecodeError as e:
            logger.warning("Bad active state JSON for %s: %s", account_id, e)
            return None
        except Exception as e:
            logger.warning("Bad active state for %s: %s", account_id, e)
            return None
    
    def create_session_participant(self, account_id: str) -> ExerciseSessionParticipant:
        participant = ExerciseSessionParticipant(
            id=account_id,
            color="#FFFFFF" # TODO - Make this dynamic
        )
        
        return participant

    async def create_session(self, account_id: str) -> Optional[ExerciseSessionInDB]:
        session = await self.get_active_session_by_user(account_id)
        if session:
            return None
        
        now = datetime.now(timezone.utc)
        participant = self.create_session_participant(account_id)
        new_session = ExerciseSession(
            owner_id=account_id,
            status=ExerciseSessionStatus.ACTIVE,
            participants=[participant],
            created_at=now,
            updated_at=now,
        )
        
        inserted = await self.mongo.insert(collection=collection_name, document=new_session.dict(by_alias=True, exclude_none=True))
        created = await self.mongo.find_one_by_id(collection=collection_name, document_id=inserted)
        
        return ExerciseSessionInDB(**created) if created else None

    async def create_session_state(self, session_id: str, account_id: str) -> Optional[ExerciseSessionState]:
        session = await self.get_session_by_id(session_id)
        if not session:
            return None
        
        existing_state = await self.get_active_session_state_by_user(account_id)
        if existing_state is not None and existing_state.session_id != session_id:
            return None
        if existing_state is not None:
            return existing_state
        
        new_state = ExerciseSessionState(
            session_id=session_id,
            account_id=account_id,
            version=0
        )
        
        key = build_state_key(session_id, account_id)
        raw = new_state.json(exclude_none=True)
        await self.redis.set(key, raw, ex=3600)
        
        return new_state
    
    async def update_session_state(self, new_state: ExerciseSessionState) -> Optional[ExerciseSessionState]:
        session = await self.get_session_by_id(new_state.session_id)
        if not session:
            return None
        
        key = build_state_key(new_state.session_id, new_state.account_id)
        raw = new_state.json(exclude_none=True)
        await self.redis.set(key, raw, ex=3600)

    async def delete_session(self, session_id: str) -> bool:
        res = await self.mongo.delete_by_id(collection=collection_name, document_id=session_id)
        return bool(getattr(res, "deleted_count", 0))

    async def delete_session_state(self, session_id: str, account_id: str) -> bool:
        key = build_state_key(session_id=session_id, account_id=account_id)
        res = await self.redis.delete(key)
        return bool(res)

    async def invite(self, session_id: str, invited_by_account_id: str, invited_account_id: str) -> bool:
        session = await self.get_session_by_id(session_id)
        if not session:
            return False
        
        invite = ExerciseSessionInvitation(
                invited=invited_account_id,
                invited_by=invited_by_account_id
            )
            
        doc = invite.dict(exclude_none=True)
        
        res = await self.mongo.update_by_id(
            collection=collection_name,
            document_id=session_id,
            update={
                "$push": {"invitations": doc},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        return bool(getattr(res, "modified_count", 0))

    async def uninvite(self, session_id: str, account_id: str) -> bool:
        res = await self.mongo.update_by_id(
            collection=collection_name,
            document_id=session_id,
            update={
                "$pull": {"invitations": {"invited": account_id}},
                "$set": {"updated_at": datetime.now(timezone.utc)}
            }
        )
        
        return bool(getattr(res, "modified_count", 0))
