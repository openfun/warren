"""Seed the experience index"""

import logging

from sqlmodel import Session, select

from sqlalchemy.exc import SQLAlchemyError

from warren.db import get_session
from warren.xi.factories import ExperienceFactory
from warren.xi.models import (
    Experience,
    Relation,
)

logger = logging.getLogger(__name__)


def seed_experience_index():
    """Seed the Experience Index with mocked data.

    The mocked data have to align with the Learning Record Store (LRS).
    Note: If there are updates to the LRS fixtures, manually update the IRI accordingly.
    """

    # Get a database session
    session = get_session()

    # Pass the database session to the factory
    ExperienceFactory.__session__ = session

    # Hardcode mocked IRIs, which match the LRS fixtures
    mocked_iri = {
                "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50",
                "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d",
                "uuid://541dab6b-50ae-4444-b230-494f0621f132",
                "uuid://69d32ad5-3af5-4160-a995-87e09da6865c",
                "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb",
                "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e",
                "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0",
                "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7",
                "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
                "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b",
                "uuid://e151ee65-7a72-478c-ac57-8a02f19e748e",
    }

    # Retrieve existing IRIs from the database
    existing_iri = {experience.iri for experience in session.exec(select(Experience)).all()}
    mocked_iri = mocked_iri - existing_iri

    # Prepare the new experiences
    new_experiences = [
        ExperienceFactory.build(
            iri=iri,
            title=f'{{"en": "lesson {i + 1}"}}',
            structure="atomic",
            aggregation_level=1
        ) for i, iri in enumerate(mocked_iri)
    ]

    # Add the new experiences to the Experience Index
    try:
        session.add_all(new_experiences)
        session.commit()
    except SQLAlchemyError:
        logging.debug("Could not seed the Experience Index. Exception:", exc_info=True)
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_experience_index()
