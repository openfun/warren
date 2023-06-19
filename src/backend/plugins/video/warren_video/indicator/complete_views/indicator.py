"""Complete views indicator : the histogram of complete views of the video."""

from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from warren_video.indicator.indicator import VideoIndicator
from warren_video.metric.histogram import histogram_metric

complete_views_indicator = VideoIndicator(
    name="complete_views",
    metric=histogram_metric,
    verb=CompletedVerb(),
)
