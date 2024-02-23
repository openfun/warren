"""Experience Index API Relations router."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from typing_extensions import Annotated  # python <3.9 compat

from warren.db import get_session
from warren.models import LTIToken
from warren.utils import get_lti_token

from ..filters import Pagination
from ..models import (
    RelationCreate,
    RelationRead,
    RelationUpdate,
)
from ..schema import Relation

router = APIRouter(
    prefix="/relations",
)

logger = logging.getLogger(__name__)


@router.get("/", response_model=List[RelationRead])
async def read_relations(
    pagination: Annotated[Pagination, Depends()],
    token: Annotated[LTIToken, Depends(get_lti_token)],
    session: Session = Depends(get_session),
):
    """Retrieve a list of relations based on query parameters.

    Args:
        pagination (Pagination): The filters for pagination (offset and limit).
        token (LTIToken): The LTI token used to authenticate user.
        session (Session, optional): The database session.

    Returns:
        List[RelationRead]: List of relations matching the query.
    """
    logger.debug("Reading relations")
    statement = select(Relation)
    relations = session.exec(
        statement.offset(pagination.offset).limit(pagination.limit)
    ).all()

    logger.debug("Results = %s", relations)
    return relations


@router.post("/", response_model=UUID)
async def create_relation(
    relation: RelationCreate,
    token: Annotated[LTIToken, Depends(get_lti_token)],
    session: Session = Depends(get_session),
):
    """Create a relation.

    Args:
        relation (Relation): The data of the relation to create.
        token (LTIToken): The LTI token used to authenticate user.
        session (Session, optional): The database session.

    Returns:
        UUID: The id of the created relation.
    """
    logger.debug("Creating a relation")
    try:
        db_relation = Relation.model_validate(relation)
    except ValidationError as exception:
        message = "An error occurred while validating the relation"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=message
        ) from exception

    session.add(db_relation)

    try:
        session.commit()
    except IntegrityError as exception:
        session.rollback()
        message = "An error occurred while creating the relation"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    logger.debug("Result = %s", db_relation.id)
    return db_relation.id


@router.put("/{relation_id}", response_model=RelationRead)
async def update_relation(
    relation_id: UUID,
    relation: RelationUpdate,
    token: Annotated[LTIToken, Depends(get_lti_token)],
    session: Session = Depends(get_session),
):
    """Update an existing relation by ID.

    Args:
        relation_id (UUID): The unique identifier of the relation to be updated.
        relation (RelationUpdate): The data to update the relation with.
        token (LTIToken): The LTI token used to authenticate user.
        session (Session, optional): The database session.

    Returns:
        RelationRead: Detailed information about the updated relation.

    """
    logger.debug("Updating the relation")
    db_relation = session.get(Relation, relation_id)

    if not db_relation:
        message = "Relation not found"
        logger.debug("%s: %s", message, relation_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    relation_data = relation.dict(exclude_none=True)
    for key, value in relation_data.items():
        setattr(db_relation, key, value)

    session.add(db_relation)

    try:
        session.commit()
    except IntegrityError as exception:
        session.rollback()
        message = "An error occurred while updating the relation"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    logger.debug("Result = %s", db_relation)
    session.refresh(db_relation)
    return db_relation


@router.get("/{relation_id}", response_model=RelationRead)
async def read_relation(
    relation_id: UUID,
    token: Annotated[LTIToken, Depends(get_lti_token)],
    session: Session = Depends(get_session),
):
    """Retrieve detailed information about a relation.

    Args:
        relation_id (IRI): The ID of the relation to retrieve.
        token (LTIToken): The LTI token used to authenticate user.
        session (Session, optional): The database session.

    Returns:
        RelationRead: Detailed information about the requested relation.
    """
    logger.debug("Reading the relation")
    relation = session.get(Relation, relation_id)
    if not relation:
        message = "Relation not found"
        logger.debug("%s: %s", message, relation_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    logger.debug("Result = %s", relation)
    return relation
