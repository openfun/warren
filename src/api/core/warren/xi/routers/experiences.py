"""Experience Index API Experiences router."""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from typing_extensions import Annotated  # python <3.9 compat

from warren.db import get_session
from warren.xi.filters import Pagination
from warren.xi.models import (
    AggregationLevel,
    Experience,
    ExperienceRead,
    ExperienceReadSnapshot,
    ExperienceUpdate,
    Structure,
)

router = APIRouter(
    prefix="/experiences",
)

logger = logging.getLogger(__name__)


@router.get("/", response_model=List[ExperienceReadSnapshot])
async def read_experiences(
    pagination: Annotated[Pagination, Depends()],
    session: Session = Depends(get_session),
    structure: Optional[Structure] = None,
    aggregation_level: Optional[AggregationLevel] = None,
):
    """Retrieve a list of experiences based on query parameters.

    Args:
        pagination (Pagination): The filters for pagination (offset and limit).
        session (Session, optional): The database session.
        structure (Structure, optional): Filter by experience structure.
        aggregation_level (AggregationLevel, optional): Filter by aggregation level.

    Returns:
        List[ExperienceReadSnapshot]: List of experiences matching the query.
    """
    logger.debug("Reading experiences")
    statement = select(Experience)
    # todo - discuss of a more 'factorized' approach of passing query params

    if structure:
        statement = statement.where(Experience.structure == structure)
    if aggregation_level:
        statement = statement.where(Experience.aggregation_level == aggregation_level)
    experiences = session.exec(
        statement.offset(pagination.offset).limit(pagination.limit)
    ).all()

    logger.debug("Results = %s", experiences)
    return experiences


@router.post("/", response_model=UUID)
async def create_experience(
    experience: Experience, session: Session = Depends(get_session)
):
    """Create an experience.

    Args:
        experience (Experience): The data of the experience to create.
        session (Session, optional): The database session.

    Returns:
        UUID: The id of the created experience.
    """
    logger.debug("Creating an experience")
    try:
        session.add(experience)
        session.commit()
    except IntegrityError as exception:
        message = "An error occurred while creating the experience"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    logger.debug("Result = %s", experience.id)
    return experience.id


@router.put("/{experience_id}", response_model=ExperienceRead)
async def update_experience(
    experience_id: UUID,
    experience: ExperienceUpdate,
    session: Session = Depends(get_session),
):
    """Update an existing experience by ID.

    Args:
        experience_id (UUID): The unique identifier of the experience to be updated.
        experience (ExperienceUpdate): The data to update the experience with.
        session (Session, optional): The database session.

    Returns:
        ExperienceRead: Detailed information about the updated experience.

    """
    logger.debug("Updating the experience")
    db_experience = session.get(Experience, experience_id)

    if not db_experience:
        message = "Experience not found"
        logger.debug("%s: %s", message, experience_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    experience_data = experience.dict(exclude_none=True)
    for key, value in experience_data.items():
        setattr(db_experience, key, value)

    try:
        session.add(db_experience)
        session.commit()
    except IntegrityError as exception:
        message = "An error occurred while updating the experience"
        logger.debug("%s: %s", message, exception)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    session.refresh(db_experience)

    logger.debug("Result = %s", db_experience)
    return db_experience


@router.get("/{experience_id}", response_model=ExperienceRead)
async def read_experience(experience_id: UUID, session: Session = Depends(get_session)):
    """Retrieve detailed information about an experience.

    Args:
        experience_id (UUID): The ID of the experience to retrieve.
        session (Session, optional): The database session.

    Returns:
        ExperienceRead: Detailed information about the requested experience.
    """
    logger.debug("Reading the experience")
    experience = session.get(Experience, experience_id)
    if not experience:
        message = "Experience not found"
        logger.debug("%s: %s", message, experience_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    logger.debug("Result = %s", experience)
    return experience
