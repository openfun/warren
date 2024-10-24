""""Warren Moodle indicators."""

from dataclasses import dataclass
from typing import List, Optional, Type, Union

from ralph.backends.lrs.base import LRSStatementsQuery
from warren.conf import settings as core_settings
from warren.indicators import (
    BaseDailyEvent,
    BaseIndicator,
    CacheMixin,
    DailyEvent,
    DailyUniqueEvent,
)
from warren.models import DailyCount, DailyUniqueCount
from warren.xi.client import ExperienceIndex
from warren.xi.exceptions import ExperienceIndexException


@dataclass
class ActivityViewsCount:
    """Total view counts of an activity."""

    iri: str
    modname: str
    views: Optional[Union[List[DailyCount], List[DailyUniqueCount]]] = None


class DailyViews(DailyEvent):
    """Daily Views indicator.

    Calculate the total and daily counts of activities' views.

    Inherit from DailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    verb_id: str = "http://id.tincanapi.com/verb/viewed"


class DailyUniqueViews(DailyUniqueEvent):
    """Daily Unique Views indicator.

    Calculate the total, unique and daily counts of activities' views.

    Inherit from DailyUniqueEvent, which provides functionality for calculating
    indicators based on different xAPI verbs and users.
    """

    verb_id: str = "http://id.tincanapi.com/verb/viewed"


class CourseDailyMixin(BaseIndicator, CacheMixin):
    """Mixin class for computing daily and unique views of course activities.

    This class provides a common interface for fetching activities and computing
    views or unique views for course-related activities.
    """

    views_indicator: Optional[Type[BaseDailyEvent]]

    def __init__(self, course_id, span_range, modname=None):
        """Instantiate the mixin for course daily indicator."""
        super().__init__(course_id=course_id, span_range=span_range, modname=modname)

    def get_lrs_query(self):
        """Construct the LRS query for statements whose object is the course.

        WARNING: this method is used only for key cache computing as the LRS
        query requires to look for statements which object is related to the course.
        """
        return LRSStatementsQuery(activity=self.course_id, until=self.until)

    async def fetch_activities(self):
        """Fetch activities related to the course from the Experience Index."""
        activities = []

        xi = ExperienceIndex(url=core_settings.XI_BASE_URL)
        course = await xi.experience.get(object_id=self.course_id)

        if course is None:
            raise ExperienceIndexException(
                f"Unknown course {self.course_id}. It should be indexed first!"
            )
        if not course.relations_target:
            raise ExperienceIndexException(
                f"No content indexed for course {self.course_id}"
            )

        for source in course.relations_target:
            content = await xi.experience.get(object_id=source.source_id)
            if content is None:
                raise ExperienceIndexException(
                    f"Failed to find content for relation for course {self.course_id}"
                )
            # If no `modname` values are specified, include all course experiences.
            # Otherwise, add only experiences for which the technical datatype
            # matches an entry in 'modname'. This filter helps ensure that only relevant
            # activity types (e.g., "video" or "quiz") are processed.
            if self.modname is None or content.technical_datatypes[0] in self.modname:
                activities.append(content)

        return activities

    async def compute(self) -> List:
        """Compute and return the views of course-related activities."""
        if self.views_indicator is None:
            raise ValueError("views_indicator must be defined in subclasses.")

        if not callable(self.views_indicator):
            raise TypeError(
                f"Expected a callable class, but got {type(self.views_indicator)}"
            )

        views_counts = []
        activities = await self.fetch_activities()
        views_class = self.views_indicator

        # Compute views for each activity and update the views field value if
        # views statements are fetched from the LRS
        for activity in activities:
            views = await views_class(
                object_id=activity.iri, span_range=self.span_range
            ).get_or_compute()
            views_counts.append(
                ActivityViewsCount(
                    iri=activity.iri,
                    modname=activity.technical_datatypes[0],
                    views=views,
                )
            )

        return views_counts


class CourseDailyViews(CourseDailyMixin):
    """Class to compute daily views for course-related activities."""

    views_indicator = DailyViews


class CourseDailyUniqueViews(CourseDailyMixin):
    """Class to compute daily unique views for course-related activities."""

    views_indicator = DailyUniqueViews
