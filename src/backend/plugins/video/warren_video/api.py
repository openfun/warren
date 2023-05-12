"""Warren API v1 video router."""

import datetime
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from warren import backends
from warren.conf import settings
from warren.fields import IRI

router = APIRouter(
    prefix="/video",
)


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    day: datetime.date
    views: int


class VideoViews(BaseModel):
    """Model to represent video views."""

    total: int
    daily_views: List[VideoDayViews]


@router.get("/{video_id:path}/views")
async def views(video_id: IRI) -> VideoViews:
    """Video views."""
    query_params = {
        "query": {
            "bool": {
                "filter": [
                    {
                        "range": {
                            (
                                "result.extensions."
                                "https://w3id.org/xapi/video/extensions/time"
                            ): {"lte": 30}
                        }
                    },
                    {
                        "term": {
                            "verb.display.en-US.keyword": "played",
                        }
                    },
                    {
                        "term": {
                            "object.id.keyword": video_id,
                        }
                    },
                ],
            }
        },
        "aggs": {
            "daily_views": {
                "date_histogram": {
                    "field": settings.ES_INDEX_TIMESTAMP_FIELD,
                    "calendar_interval": "day",
                }
            }
        },
        "size": 0,
    }
    docs = await backends.es_client.search(
        **query_params,
        index=settings.ES_INDEX,
    )
    video_views = VideoViews(total=docs["hits"]["total"]["value"], daily_views=[])
    for bucket in docs["aggregations"]["daily_views"]["buckets"]:
        video_views.daily_views.append(
            VideoDayViews(day=bucket["key"], views=bucket["doc_count"])
        )
    return video_views
