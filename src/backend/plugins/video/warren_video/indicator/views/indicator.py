"""Views indicator : the histogram of views of the video."""

from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren_video.indicator.indicator import VideoIndicator
from warren_video.metric.histogram import histogram_metric
from warren_video.statement_filters import filter_played_views

views_indicator = VideoIndicator(
    name="views",
    verb=PlayedVerb(),
    metric=histogram_metric,
    filter_callback=filter_played_views,
)
