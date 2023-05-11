"""Warren API v1 video router."""

import re
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

import dateparser
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, root_validator, validator

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


class DateRangeModel(BaseModel):
    since: Optional[str] = "last week"
    until: Optional[str] = "now"
    parsed_since: Optional[datetime] = None
    parsed_until: Optional[datetime] = None

    def validate_date_string(value: str, param_name: str) -> str:
        if value == "":
            raise HTTPException(
                status_code=400,
                detail=f"Date parsing error: '{param_name}' can't be an empty",
            )
        parsed_time = dateparser.parse(
            value, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Z"}
        )
        if parsed_time is None:
            # raise ValueError("Could not parse time input")
            raise HTTPException(
                status_code=400,
                detail=f"Date parsing error: Could not parse parameter '{param_name}'",
            )
        return value

    def parse_since_date(since: str) -> datetime:
        return dateparser.parse(
            since, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Z"}
        )

    def parse_until_date(until: str, since: datetime) -> datetime:
        parsed_input_date = dateparser.parse(
            until, settings={"RETURN_AS_TIMEZONE_AWARE": True, "TIMEZONE": "Z"}
        )

        if parsed_input_date:
            # check if we have a timedelta or a date
            # timedelta are in the format <number><unit>
            # like  7d, 4weeks ...
            pattern = r"\d+[a-zA-Z]+"
            if bool(re.fullmatch(pattern, until)):
                delta = datetime.now(timezone.utc) - parsed_input_date
                parsed_until = since + delta
            else:
                # parsed_until = dateparser.parse(parsed_until)
                parsed_until = parsed_input_date
        return parsed_until

    @validator("since", pre=True)
    def validate_since_string(cls, value):
        return cls.validate_date_string(value, "since")

    @validator("until", pre=True)
    def validate_until_string(cls, value):
        return cls.validate_date_string(value, "until")

    @root_validator(pre=False)
    def parse_dates_and_validate_range(cls, values):
        values["parsed_since"] = cls.parse_since_date(values.get("since"))
        values["parsed_until"] = cls.parse_until_date(
            values.get("until"), values["parsed_since"]
        )

        if values["parsed_until"] < values["parsed_since"]:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid time range: 'until' parameter should be more recent"
                    "( i.e. greater or equal ) to the 'since' parameter."
                    "'until' default value is 'now' and"
                    "'since' default value is 'one week ago'"
                ),
            )
        return values


@router.get("/{video_id:path}/views")
async def views(video_id: IRI, date_range: DateRangeModel = Depends()) -> VideoViews:
    """Video views."""

    until = date_range.parsed_until
    since = date_range.parsed_since

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

    for d in date_range:
        date_ts = int(datetime(d.year, d.month, d.day).timestamp()) * 1000
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
