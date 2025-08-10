from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import HTTPBearer
from typing import Dict, Any, List, Optional
import logging

from app.deps import read_request_account_id, get_mongo, get_redis
from app.db.mongo import Mongo
from app.db.redis import Redis
from app.repos.exercise import ExerciseMetaRepository
from app.schema.exercise import ExerciseMetaInDB, ExerciseMuscleGroup, ExerciseEquipment
from app.models.requests.exercise import ExerciseMetaCreateRequest
from app.util.sanitize import sanitize_str, sanitize_str_list
from app.models.responses.base import ErrorResponse

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
    "/meta/id/{identifier}",
    response_model=ExerciseMetaInDB,
    summary="Get exercise meta by ID",
    responses={
        404: {"model": ErrorResponse, "description": "Exercise not found"}
    }
)
async def get_exercise_meta_by_id(
    identifier: str,
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
) -> ExerciseMetaInDB:
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        res = await repo.get_exercise_by_id(identifier)
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")    
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exercise by ID: {identifier}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/meta/name/{name}",
    response_model=ExerciseMetaInDB,
    summary="Get exercise by name",
    responses={
        404: {"model": ErrorResponse, "description": "Exercise not found"}
    }
)
async def get_exercise_meta_by_name(
    name: str,
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    try:
        sanitized = sanitize_str(name)
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        res = await repo.get_exercise_by_name(sanitized)
        
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get exercise meta by name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/meta/muscle-group/{group}",
    response_model=List[ExerciseMetaInDB],
    summary="Get exercises by muscle group",
)
async def get_exercises_by_muscle_group(
    muscle_group: ExerciseMuscleGroup,
    limit: int = Query(default=50, ge=1, le=100),
    verified_only: bool = Query(default=False),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        exercises = await repo.get_exercises_by_muscle_group(
            muscle_group=muscle_group,
            limit=limit,
            verified_only=verified_only
        )
        return exercises
    except Exception as e:
        logger.error(f"Failed to get exercises by muscle group {muscle_group}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/meta/equipment/{equipment}",
    response_model=List[ExerciseMetaInDB],
    summary="Get exercises by equipment",
)
async def get_exercises_by_equipment(
    equipment: ExerciseEquipment,
    limit: int = Query(default=50, ge=1, le=100),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        exercises = await repo.get_exercises_by_equipment(
            equipment=equipment,
            limit=limit
        )
        return exercises
    except Exception as e:
        logger.error(f"Failed to get exercises by equipment {equipment}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get(
    "/meta/search",
    status_code=status.HTTP_200_OK,
    response_model=List[ExerciseMetaInDB],
    summary="Search for exercise meta",
    responses={
        404: {"model": ErrorResponse, "description": "Exercises not found"},
    }
)
async def search_exercise_meta(
    q: str = Query(..., min_length=2, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=50, description="Maximum number of results"),
    include_aliases: bool = Query(default=True, description="Include aliases in search"),
    verified_only: bool = Query(default=False, description="Only return verified exercises"),
    muscle_group: Optional[ExerciseMuscleGroup] = Query(default=None, description="Filter by muscle group"),
    equipment: Optional[ExerciseEquipment] = Query(default=None, description="Filter by equipment"),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis),
):
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        
        if muscle_group and not equipment:
            exercises = await repo.get_exercises_by_muscle_group(
                muscle_group=muscle_group,
                limit=limit,
                verified_only=verified_only
            )
        elif equipment and not muscle_group:
            exercises = await repo.get_exercises_by_equipment(
                equipment=equipment,
                limit=limit
            )
        else:
            exercises = await repo.get_exercises_by_fuzzy_search(
                query=q,
                limit=limit,
                include_aliases=include_aliases
            )
            
            if muscle_group:
                exercises = [ex for ex in exercises if muscle_group in (ex.muscle_groups or [])]
            if equipment:
                exercises = [ex for ex in exercises if ex.equipment == equipment]
            if verified_only:
                exercises = [ex for ex in exercises if ex.verified]
        
        if not exercises:
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No exercises found"
            )
            
        return exercises
    except Exception as e:
        logger.error(f"Failed to search exercises with query '{q}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post(
    "/meta/",
    response_model=ExerciseMetaInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create new exercise meta",
    responses={
        409: {"model": ErrorResponse, "description": "Exercise with this name already exists"},
        422: {"model": ErrorResponse, "description": "Validation error"}
    }
)
async def create_exercise_meta(
    req: ExerciseMetaCreateRequest,
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
) -> ExerciseMetaInDB:
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
    
        existing = await repo.get_exercise_by_name(req.name)
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Exercise with this name already exists")
        
        sanitized_name = sanitize_str(req.name)
        sanitized_aliases = sanitize_str_list(req.aliases) if req.aliases else []
        
        new_meta = await repo.create_exercise(
            name=sanitized_name,
            created_by=current_user["id"],
            aliases=sanitized_aliases,
            muscle_groups=req.muscle_groups,
            equipment=req.equipment,
        )
        
        if not new_meta:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create exercise meta")    
        return new_meta
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create exercise meta: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put(
    "/meta/{identifier}",
    response_model=ExerciseMetaInDB,
    summary="Update exercise",
    description="Update an existing exercise metadata entry"
)
async def update_exercise_meta(
    identifier: str,
    updates: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(read_request_account_id),
    mongo: Mongo = Depends(get_mongo),
    redis: Redis = Depends(get_redis)
):
    try:
        repo = ExerciseMetaRepository(mongo=mongo, redis=redis)
        
        existing = await repo.get_exercise_by_id(identifier)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        # check permissions - only creator or admin can update
        # for now only allow creator to update
        if existing.created_by != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update exercises you created"
            )
        
        if "name" in updates:
            updates["name"] = sanitize_str(updates["name"])
        if "aliases" in updates:
            updates["aliases"] = sanitize_str_list(updates["aliases"])
        
        # remove fields that shouldn't be updated by users
        forbidden_fields = ["id", "_id", "created_by", "created_at", "verified", "uses"]
        for field in forbidden_fields:
            updates.pop(field, None)
        
        updated_exercise = await repo.update_exercise(identifier, updates)
        if not updated_exercise:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update exercise"
            )
        
        logger.info(f"Updated exercise {identifier} by user {current_user['username']}")
        return updated_exercise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update exercise {identifier}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.delete(
    "/meta/{identifier}"
)
async def delete_exercise_meta():
    pass