"""Tests for the video API endpoints."""

import pytest
from httpx import AsyncClient

from warren.api import app
from warren.conf import settings


@pytest.mark.asyncio
async def test_views_video_id_path(es):
    """Test the video views endpoint "video_id" path validity."""

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo/views")
    assert response.status_code == 422
    assert response.json().get("detail")[0].get("msg") == "'foo' is not a valid 'IRI'."

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo/bar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg") == "'foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video//foo/bar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == "'/foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo%2Fbar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg") == "'foo/bar' is not a valid 'IRI'."
    )

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/%2Ffoo%2Fbar/views")
    assert response.status_code == 422
    assert (
        response.json().get("detail")[0].get("msg")
        == "'/foo/bar' is not a valid 'IRI'."
    )

    no_statements_response = {"daily_views": [], "total": 0}

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/http://foo/bar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/http%3A%2F%2Ffoo%2Fbar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/uuid://foo/bar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/uuid%3A%2F%2Ffoo%2Fbar/views")
    assert response.status_code == 200
    assert response.json() == no_statements_response


from pydantic_factories import ModelFactory, Use
from ralph.models.xapi.fields.unnested_objects import ActivityObjectField
from ralph.models.xapi.fields.actors import (
    ActorField,
    AccountActorField,
    AccountActorAccountField,
)
from ralph.models.xapi.video.fields.objects import (
    VideoObjectField,
    VideoObjectDefinitionField,
)
from ralph.models.xapi.video.fields.results import VideoPlayedResultField
from ralph.models.xapi.video.statements import VideoPlayed


class AccountActorAccountFieldFactory(ModelFactory):
    __model__ = AccountActorAccountField
    __auto_register__ = True

    homePage: str = "http://lms.example.org"
    name: str = "john_doe"


class AccountActorFieldFactory(ModelFactory):
    __model__ = AccountActorField
    __auto_register__ = True

    account = Use(AccountActorAccountFieldFactory.build)


class VideoObjectDefinitionFieldFactory(ModelFactory):
    __model__ = VideoObjectDefinitionField
    __auto_register__ = True

    name = {"en-US": "Video"}
    description = {"en-US": "Video activity"}


class VideoObjectFieldFactory(ModelFactory):
    __model__ = VideoObjectField
    __auto_register__ = True

    id = "uuid://0fe19425-9ff5-494d-bdf9-2938aa6c1030"
    name = {"en-US": "Some random Video"}
    definition = Use(VideoObjectDefinitionFieldFactory.build)


class VideoPlayedResultFieldFactory(ModelFactory):
    __model__ = VideoPlayedResultField
    __auto_register__ = True

    score = None
    success = None
    completion = None
    response = None
    duration = None
    extensions = {"https://w3id.org/xapi/video/extensions/time": 3.2}


class MyVideoPlayed(VideoPlayed):
    class Config:
        smart_union = True


class VideoPlayedFactory(ModelFactory):

    __model__ = MyVideoPlayed
    __allow_none_optionals__ = False

    actor = Use(AccountActorFieldFactory.build)
    object = Use(VideoObjectFieldFactory.build)
    result = Use(VideoPlayedResultFieldFactory.build)


@pytest.mark.asyncio
async def test_views_backend_query(es):
    """Test the video views endpoint backend query results."""

    # Idea try to mix factory declarations and Pydantic model instantiation
    print(AccountActorFieldFactory.build(name="foo").dict())
    print(
        VideoPlayed(
            actor=AccountActorFieldFactory.build(name="foo").dict(),
            object=VideoObjectFieldFactory.build().dict(),
            result=VideoPlayedResultFieldFactory.build(score=12).dict(),
        )
    )
    statement = VideoPlayedFactory.build(
        actor=AccountActorFieldFactory.build().dict(),
        factory_use_construct=True,
    )
    print(statement.dict())
    assert False

    async with AsyncClient(app=app, base_url=settings.SERVER_URL) as client:
        response = await client.get("/api/v1/video/foo/views")
    assert response.status_code == 422
    assert response.json().get("detail")[0].get("msg") == "'foo' is not a valid 'IRI'."
