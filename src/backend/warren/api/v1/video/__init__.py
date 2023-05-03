"""Warren API v1 video router."""

from datetime import datetime, date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from warren import backends
from warren.conf import settings
from warren.fields import IRI

router = APIRouter(
    prefix="/video",
)


class VideoDayViews(BaseModel):
    """Model to represent video views for a date."""

    day: date
    views: int


class VideoViews(BaseModel):
    """Model to represent video views."""

    total: int
    daily_views: List[VideoDayViews]


def days_between(since: datetime, until: datetime) -> int:
    return (until.date() - since.date()).days + 1


@router.get("/{video_id:path}/views")
async def views(
    video_id: IRI,
    since: Optional[datetime] = Query(
        None,
        description=(
            "Filter events that occurred after that timestamp (included)"
        ),
    ),
    until: Optional[datetime] = Query(
        None,
        description=(
            "Filter events that occurred before that timestamp (included)"
        ),
    ),
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
                        },
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
                    {"range": {"timestamp": {"gte": since}}},
                    {"range": {"timestamp": {"lte": until}}},
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

    buckets = docs["aggregations"]["daily_views"]["buckets"]
    video_views = VideoViews(total=docs["hits"]["total"]["value"], daily_views=[])

    # sync the buckets and received date range
    # as ES "trim" the buckets from videos with 0 views,
    # sometime not all the date from the date_range are
    # contained in the buckets ( len(buckets) <= len(date_range))

    date_range = [
        since.date() + timedelta(days=i)
        for i in range((until.date() - since.date()).days + 1)
    ]  # +1 for an inclusive range
    for date in date_range:
        date_ts = int(datetime(date.year, date.month, date.day).timestamp()) * 1000
        # TODO: could improve performance by not using a filter
        bucket = list(filter(lambda v: v["key"] == date_ts, buckets))
        if len(bucket) == 1:
            video_views.daily_views.append(
                VideoDayViews(day=date_ts, views=bucket[0]["doc_count"])
            )
        elif len(bucket) == 0:
            video_views.daily_views.append(VideoDayViews(day=date_ts, views=0))
        else:
            raise ValueError(("filtered bucket should return only one or zero element"))

    return video_views
