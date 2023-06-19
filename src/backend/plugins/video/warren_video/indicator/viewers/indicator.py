"""Viewers indicator : the total of viewers who played the video."""

from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren_video.indicator.indicator import VideoIndicator
from warren_video.metric.count import count_metric
from warren_video.statement_filters import filter_played_views

viewers_indicator = VideoIndicator(
    name="viewers",
    verb=PlayedVerb(),
    metric=count_metric,
    filter_callback=filter_played_views,
)
