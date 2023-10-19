"""Experience Index API Relations router."""
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from typing_extensions import Annotated  # python <3.9 compat

from warren.db import get_session
from warren.xi.filters import Pagination
from warren.xi.models import (
    Relation,
    RelationRead,
    RelationUpdate,
)

router = APIRouter(
    prefix="/relations",
)

logger = logging.getLogger(__name__)


@router.get("/")
async def read_relations(
    pagination: Annotated[Pagination, Depends()],
    session: Session = Depends(get_session),
) -> List[RelationRead]:
    """Retrieve a list of relations based on query parameters.

    Args:
        pagination (Pagination): The filters for pagination (offset and limit).
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


@router.post("/")
async def create_relation(
    relation: Relation, session: Session = Depends(get_session)
) -> UUID:
    """Create a relation.

    Args:
        relation (Relation): The data of the relation to create.
        session (Session, optional): The database session.

    Returns:
        UUID: The id of the created relation.
    """
    logger.debug("Creating a relation")
    try:
        session.add(relation)
        session.commit()
    except IntegrityError as exception:
        message = "An error occurred while creating the relation"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    logger.debug("Result = %s", relation.id)
    return relation.id


@router.put("/{relation_id}")
async def update_relation(
    relation_id: UUID, relation: RelationUpdate, session: Session = Depends(get_session)
) -> RelationRead:
    """Update an existing relation by ID.

    Args:
        relation_id (UUID): The unique identifier of the relation to be updated.
        relation (RelationUpdate): The data to update the relation with.
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

    try:
        session.add(db_relation)
        session.commit()
    except IntegrityError as exception:
        message = "An error occurred while updating the relation"
        logger.debug("%s. Exception:", message, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message
        ) from exception

    logger.debug("Result = %s", db_relation)
    session.refresh(db_relation)
    return db_relation


@router.get("/{relation_id}")
async def read_relation(
    relation_id: UUID, session: Session = Depends(get_session)
) -> RelationRead:
    """Retrieve detailed information about a relation.

    Args:
        relation_id (IRI): The ID of the relation to retrieve.
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
