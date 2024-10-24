""""Warren Moodle indicators."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Union

from ralph.backends.lrs.base import LRSStatementsQuery
from warren.indicators import BaseIndicator, CacheMixin, DailyEvent, DailyUniqueEvent
from warren.models import DailyCount, DailyUniqueCount
from warren.xi.client import ExperienceIndex
from warren.xi.exceptions import ExperienceIndexException

from .conf import settings as moodle_plugin_settings


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

    def __init__(self, course_id, span_range, modname=None):
        """Instantiate the mixin for course daily indicator."""
        super().__init__(course_id=course_id, span_range=span_range, modname=modname)

    def get_lrs_query(self):
        """Construct the LRS query for statements whose object is the course.

        WARNING: this method is used only for key cache computing as the LRS
        query requires to look for statements which object is related to the course.
        """
        return LRSStatementsQuery(activity=self.course_id, until=self.until)

    @abstractmethod
    def get_views_indicator_class(self):
        """Return the views indicator class."""
        pass

    async def fetch_activities(self):
        """Fetch activities related to the course from the Experience Index."""
        activities = []

        xi = ExperienceIndex(url=moodle_plugin_settings.BASE_XI_URL)
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
            if self.modname is None or content.technical_datatypes[0] in self.modname:
                activities.append(content)

        return activities

    async def compute(self) -> List:
        """Compute and return the views of course-related activities."""
        views_counts = []
        activities = await self.fetch_activities()
        views_class = self.get_views_indicator_class()

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

    def get_views_indicator_class(self):
        """Return the DailyViews class for calculating views."""
        return DailyViews


class CourseDailyUniqueViews(CourseDailyMixin):
    """Class to compute daily unique views for course-related activities."""

    def get_views_indicator_class(self):
        """Return the DailyUniqueViews class for calculating unique views."""
        return DailyUniqueViews
