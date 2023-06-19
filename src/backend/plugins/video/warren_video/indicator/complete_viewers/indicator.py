"""Complete viewers indicator : the total of viewers who completed the video."""

from ralph.models.xapi.concepts.verbs.scorm_profile import CompletedVerb
from warren_video.indicator.indicator import VideoIndicator
from warren_video.metric.count import count_metric

complete_viewers_indicator = VideoIndicator(
    name="complete_viewers",
    metric=count_metric,
    verb=CompletedVerb(),
)
