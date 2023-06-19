"""Warren API v1 video router."""

from typing import List

import arrow
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing_extensions import Annotated  # python <3.9 compat

from warren import backends
from warren.conf import settings
from warren.fields import IRI, Date
from warren.filters import BaseQueryFilters

router = APIRouter(
    prefix="/video",
)


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    day: Date
    views: int = 0

    def __add__(self, other):
        """Emulates addition, left member."""
        return self.views + other

    def __radd__(self, other):
        """Emulates addition, right member."""
        return self.views + other


class VideoViews(BaseModel):
    """Model to represent video views."""

    total: int
    daily_views: List[VideoDayViews]


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI, filters: Annotated[BaseQueryFilters, Depends()]
) -> VideoViews:
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
                    {"range": {"timestamp": {"gte": filters.since}}},
                    {"range": {"timestamp": {"lte": filters.until}}},
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
    video_views = VideoViews(
        total=docs["hits"]["total"]["value"],
        daily_views=[
            VideoDayViews(day=day.format("YYYY-MM-DD"))
            for day in arrow.Arrow.range("day", filters.since, filters.until)
        ],
    )

    # Daily views buckets are supposed to be sorted by date range from the
    # oldest to the newest record
    idx = 0
    for bucket in docs["aggregations"]["daily_views"]["buckets"]:
        idx = video_views.daily_views.index(VideoDayViews(day=bucket["key"]), idx)
        video_views.daily_views[idx].views = bucket["doc_count"]
    return video_views
