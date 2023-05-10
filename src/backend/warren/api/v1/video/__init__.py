"""Warren API v1 video router."""

import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

import dateparser
from fastapi import APIRouter, HTTPException, Query
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
    since: Optional[str] = Query(
        None,
        description=("Filter events that occurred after that timestamp (included)"),
    ),
    until: Optional[str] = Query(
        None,
        description=("Filter events that occurred before that timestamp (included)"),
    ),
) -> VideoViews:
    """Video views."""

    # parse date as string to datetime
    if since is None:
        since = datetime.now() - timedelta(weeks=1)
    elif since == "":
        raise HTTPException(
            status_code=400, detail="Date parsing error: 'since' can't be an empty"
        )
    else:
        since = dateparser.parse(since)
        if not since:  #
            raise HTTPException(
                status_code=400,
                detail="Date parsing error: Could not parse parameter 'since'",
            )
    if until is None:
        until = datetime.now()
    elif until == "":
        raise HTTPException(
            status_code=400,
            detail="Date parsing error: 'until' can't be an empty string",
        )
    else:
        parsed_date_input = dateparser.parse(
            until, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Z"}
        )
        if parsed_date_input:
            # check if we have a timedelta or a date
            # timedelta are in the format <number><unit>
            # like  7d, 4weeks ...
            pattern = r"\d+[a-zA-Z]+"
            if bool(re.fullmatch(pattern, until)):
                delta = datetime.now(timezone.utc) - parsed_date_input
                until = since + delta
            else:
                # until = dateparser.parse(until)
                until = parsed_date_input
        else:
            # could parse user input
            raise HTTPException(
                status_code=400,
                detail="Date parsing error: Could not parse parameter 'until'",
            )

    if until < since:
        raise HTTPException(
            status_code=400,
            detail="Invalid time range: 'until' parameter should be greater than or equal to the 'since' parameter. Until default value is 'now' and Since default value is 'one week ago'",
        )

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

    # buckets_dict = {bucket["key"]: bucket for bucket in buckets}

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
