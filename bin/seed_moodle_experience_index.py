"""Seed the experience index."""

import json
import logging
import sys
from io import TextIOWrapper
from itertools import batched
from pathlib import Path
from typing import Generator, Tuple

import pandas as pd
from pydantic import AnyUrl, BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import select

from warren.db import get_engine, get_session
from warren.xi.enums import AggregationLevel, RelationType
from warren.xi.factories import ExperienceFactory
from warren.xi.schema import Experience, Relation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

COURSE_TYPE_IRI = "http://id.tincanapi.com/activitytype/lms/course"


class Course(BaseModel):
    """Moodle course."""

    name: str
    iri: AnyUrl


class Action(BaseModel):
    """Moodle action (resource or activity)."""

    name: str
    iri: AnyUrl


def parse_statements(
    stream: TextIOWrapper,
) -> Generator[Tuple[Course, Action], None, None]:
    """Parse statements to get course and related object IDs."""
    languages = ["en", "fr"]
    for i, line in enumerate(stream):
        statement = json.loads(line)

        # Get course data
        course = None
        if "context" not in statement:
            logger.warning(
                "No context: dropping incomplete statement in row %d, dropping incomplete statement",
                i + 1,
            )
            logger.debug("Incomplete dropped statement: %s", statement)
            continue
        if "grouping" not in statement["context"]["contextActivities"]:
            logger.warning(
                "No context activities grouping in row %d, dropping incomplete statement",
                i + 1,
            )
            logger.debug("Incomplete dropped statement: %s", statement)
            continue
        for group in statement["context"]["contextActivities"]["grouping"]:
            if group["definition"]["type"] != COURSE_TYPE_IRI:
                continue
            for language in languages:
                if language not in group["definition"]["name"]:
                    continue
                course = Course(
                    name=group["definition"]["name"][language], iri=group["id"]
                )
        if course is None:
            logger.warning(
                "No course definition in row %d, dropping incomplete statement", i + 1
            )
            logger.debug("Incomplete dropped statement: %s", statement)
            continue

        # Get action for this course
        name = None
        if "name" in statement["object"]["definition"]:
            for language in languages:
                if language not in statement["object"]["definition"]["name"]:
                    continue
                name = statement["object"]["definition"]["name"][language]
        # Fallback
        elif "type" in statement["object"]["definition"]:
            name = statement["object"]["definition"]["type"]
        else:
            logger.warning(
                "Incomplete object definition in row %d, dropping incomplete statement",
                i + 1,
            )
            logger.debug("Incomplete dropped statement: %s", statement)
            continue

        action = Action(
            name=name,
            iri=statement["object"]["id"],
        )
        logger.debug("Action: %s", action)

        yield (course, action)


def seed_experience_index(course_actions: Generator[Tuple[Course, Action], None, None]):
    """Seed the Experience Index with xAPI statements.

    Note: If there are updates to the LRS fixtures, manually update the experiences or relations
    accordingly.
    """

    # Get a database session
    session = get_session()
    engine = get_engine()

    # Pass the database session to factories
    ExperienceFactory.__session__ = session

    courses = set()
    actions = set()
    experiences = []
    course_action_iris = []

    for course, action in course_actions:
        # Create a new experience for this course
        if course.iri not in courses:
            logger.debug(
                "Will create Experience for course: %s with iri: %s",
                course.name,
                course.iri,
            )
            experiences += [
                ExperienceFactory.build(
                    iri=course.iri,
                    structure="atomic",
                    aggregation_level=AggregationLevel.THREE,
                )
            ]
            courses.add(course.iri)

        if action.iri in actions:
            continue

        # Create a new experience for this action
        logger.debug(
            "Will create Experience for action: %s with iri: %s",
            action.name,
            action.iri,
        )
        experiences += [
            ExperienceFactory.build(
                iri=action.iri,
                structure="atomic",
                aggregation_level=AggregationLevel.ONE,
            )
        ]
        actions.add(action.iri)
        course_action_iris += [(course.iri, action.iri)]

    logger.info(
        "Will create %d experiences (%d courses + %d actions)",
        len(experiences),
        len(courses),
        len(actions),
    )
    logger.debug("Courses IRIs: %s", courses)
    logger.debug("Actions IRIs: %s", actions)
    # Add the new experiences to the Experience Index
    batch_size = 1000
    try:
        for i, batch in enumerate(batched(experiences, batch_size)):
            logger.info("Inserting batch %d (size: %d)", i, batch_size)
            session.add_all(batch)
            session.flush()
        session.commit()
    except SQLAlchemyError:
        logging.error("Could not create Experiences. Rolling back database session.")
        session.rollback()
        session.close()
        raise

    logger.info("Created %d experiences", len(experiences))

    logger.info("Fetching related course/action IDs")
    # Get courses and actions from the database
    db_courses = pd.read_sql(
        sql=select(Experience)
        .where(Experience.aggregation_level == AggregationLevel.THREE)
        .order_by(Experience.iri.asc()),
        con=engine,
    )
    db_actions = pd.read_sql(
        sql=select(Experience)
        .where(Experience.aggregation_level == AggregationLevel.ONE)
        .order_by(Experience.iri.asc()),
        con=engine,
    )
    # Create a dataframe from course/action IRIs
    course_action_iris = pd.DataFrame(course_action_iris, columns=["course", "action"])
    # Iterate over course/action dataframe by chunks
    course_action_relations = pd.DataFrame(columns=["course_id", "action_id"])
    chunk_size = 1000
    for idx in range(0, course_action_iris.shape[0], chunk_size):
        logger.info(
            "Create course/action IDs dataframe for chunk %d (size: %d)",
            idx,
            chunk_size,
        )
        # Add course IDs from database given course IRIs
        tmp_relations = pd.merge(
            db_courses[["id", "iri"]],
            course_action_iris[idx : idx + chunk_size],
            left_on="iri",
            right_on="course",
            how="right",
        )
        # Remove course IRI columns
        tmp_relations.drop(["iri", "course"], axis=1, inplace=True)
        # Rename `id` column to `course_id`
        tmp_relations.rename(columns={"id": "course_id"}, inplace=True)
        # Add action IDs from database given action IRIs
        tmp_relations = pd.merge(
            db_actions[["id", "iri"]],
            tmp_relations,
            left_on="iri",
            right_on="action",
            how="right",
        )
        # Remove action IRIs columns
        tmp_relations.drop(["iri", "action"], axis=1, inplace=True)
        # Rename `id` column to `action_id`
        tmp_relations.rename(columns={"id": "action_id"}, inplace=True)
        # Append to the end of the dataframe
        course_action_relations = pd.concat(
            [course_action_relations, tmp_relations], ignore_index=True
        )

    logger.info("Create Relation %d objects", course_action_relations.shape[0])
    relations = []
    for relation in course_action_relations.itertuples():
        relations += [
            Relation(
                source_id=relation.course_id,
                target_id=relation.action_id,
                kind=RelationType.HASPART,
            ),
            Relation(
                source_id=relation.action_id,
                target_id=relation.course_id,
                kind=RelationType.ISPARTOF,
            ),
        ]

    logger.info("Will create %d relations", len(relations))
    batch_size = 1000
    # Create new relations
    try:
        for i, batch in enumerate(batched(relations, batch_size)):
            logger.info("Inserting batch %d (size: %d)", i, batch_size)
            session.add_all(relations)
            session.flush()
        session.commit()
    except SQLAlchemyError:
        logging.error(
            "Could not seed the Experience Index. Rolling back database session."
        )
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    """Read statements from an archive and seed the experience index.

    Usage: python seed_experience_index.py [ARCHIVE]

    If no archive is provided, the script will read statements from stdin.
    """
    stream = sys.stdin
    if len(sys.argv) == 2:
        logger.info("Reading statements from archive: %s", sys.argv[1])
        stream = Path(sys.argv[1]).open()
    else:
        logger.info("Reading statements from stdin")

    seed_experience_index(parse_statements(stream))
