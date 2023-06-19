"""Represents a statistical indicator for a video."""

from dataclasses import dataclass
from typing import Callable, Dict, Type, get_type_hints

from pydantic import BaseModel
from ralph.models.xapi.base.verbs import BaseXapiVerb
from warren_video.metric.metric import METRIC


@dataclass(frozen=True)
class VideoIndicator:
    """Container describing a video indicator.

    Attributes:
        name (str): name of the indicator also used to determine the api endpoint
        verb (BaseXapiVerb): verb used in the lrs query to search statements
        metrics (METRIC): how we generate the metric value for this indicator
        filter_callback (Callable[[Dict], bool]): optional callback to filter statements
        before processing the metric
    """

    name: str
    verb: BaseXapiVerb
    metric: METRIC
    filter_callback: Callable[[Dict], bool] = None

    def __repr__(self):
        """Video indicator representation."""
        return f"VideoIndicator(name={self.name}, verb={self.verb.id})"

    @property
    def return_type(self) -> Type[BaseModel]:
        """Returns the type of the metric returned by the indicator."""
        return get_type_hints(self.metric).get("return")
