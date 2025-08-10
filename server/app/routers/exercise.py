from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

from app.deps import read_request_account_id, get_mongo, get_redis
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.repos.exercise import ExerciseMetaRepository
from app.schema.exercise import ExerciseMetaInDB, ExerciseMeta
from app.models.requests.exercise import ExerciseMetaCreateRequest
from app.util.sanitize import sanitize_str, sanitize_str_list

# GET
# /meta/id/{identifier}     - Get exercise by ID
# /meta/name/{name}         - Get exercise by Name
# /meta/search?query=       - Get exercises by fuzzy search
# /meta/
#
# POST
# /meta/                    - Create a new exercise meta
#
# UPDATE
# /meta/                    - Update an existing exercise meta
#
# DELETE
# /meta/{identifier}        - Delete an existing exercise meta

router = APIRouter()
logger = logging.getLogger(__name__)
security = HTTPBearer()

@router.get(
    "/meta/id/{identifier}"
)
async def get_exercise_meta_by_id(
    identifier: str,
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
    res = await repo.get_exercise_by_id(identifier)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")    
    return res

@router.get(
    "/meta/name/{name}"
)
async def get_exercise_meta_by_name(
    name: str,
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    sanitized = sanitize_str(name)
    repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
    res = await repo.get_exercise_by_name(sanitized)
    
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
    return res

@router.get(
    "/meta/search"
)
async def get_exercise_meta_by_search():
    pass

@router.post(
    "/meta/",
    response_model=ExerciseMetaInDB,
    status_code=status.HTTP_201_CREATED
)
async def create_exercise_meta(
    req: ExerciseMetaCreateRequest,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
) -> ExerciseMetaInDB:
    repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
    
    existing = await repo.get_exercise_by_name(req.name)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exercise with this name already exists")
    
    sanitized_name = sanitize_str(req.name)
    sanitized_aliases = sanitize_str_list(req.aliases) if req.aliases is not None else []
    
    new_meta = await repo.create_exercise(
        name=sanitized_name,
        created_by=current_user["id"],
        aliases=sanitized_aliases
    )
    
    if not new_meta:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create exercise meta")    
    return new_meta

@router.put(
    "/meta/"
)
async def update_exercise_meta():
    pass

@router.delete(
    "/meta/{identifier}"
)
async def delete_exercise_meta():
    pass