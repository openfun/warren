"""Seed the experience index"""

import asyncio
import logging
from urllib.parse import quote

from warren.xi.client import ExperienceIndex
from warren.xi.enums import AggregationLevel, RelationType, Structure
from warren.xi.models import ExperienceCreate

logger = logging.getLogger(__name__)


async def seed_experience_index():
    """Seed the Experience Index with mocked data.

    The mocked data have to align with the Learning Record Store (LRS).
    Note: If there are updates to the LRS fixtures, manually update the IRI accordingly.
    """
    # XI Client using default development XI base URL
    xi = ExperienceIndex()

    course_create = ExperienceCreate(
        iri="uuid://" + quote("course-v1:openfun+mathematics101+session01"),
        title={"en": "Mathematics 101"},
        language="en",
        description={"en": "lorem ipsum"},
        technical_datatypes=[
            "text/html",
        ],
        structure=Structure.ATOMIC,
        aggregation_level=AggregationLevel.THREE,
    )
    course = await xi.experience.create_or_update(course_create)
    course_title = course.title.get("en")

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

    for idx, iri in enumerate(mocked_iri):
        video_create = ExperienceCreate(
            iri=iri,
            title={"en": f"Video {idx}"},
            language="en",
            description={"en": f"Video {idx} of the {course_title} course"},
            technical_datatypes=[
                "video/mp4",
            ],
            structure=Structure.ATOMIC,
            aggregation_level=AggregationLevel.ONE,
        )
        video = await xi.experience.create_or_update(video_create)
        await xi.relation.create_bidirectional(
            source_id=course.id,
            target_id=video.id,
            kinds=[RelationType.HASPART, RelationType.ISPARTOF],
        )


if __name__ == "__main__":
    asyncio.run(seed_experience_index())
