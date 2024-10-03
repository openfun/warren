""""Warren Moodle indicators."""

from abc import abstractmethod
from dataclasses import dataclass
from typing import List

from ralph.backends.lrs.base import LRSStatementsQuery
from warren.indicators import BaseIndicator, CacheMixin, DailyEvent, DailyUniqueEvent
from warren.xi import ExperienceIndex
from warren.xi.exceptions import ExperienceIndexException

from .conf import settings as moodle_plugin_settings


@dataclass
class ActivityViews:
    """Total view counts of an activity."""
    id: str
    modname: str
    views: int = 0  # Default views is set to 0


@dataclass
class ActivityUniqueViews:
    """Unique view counts of an activity."""
    id: str
    modname: str
    unique_views: int = 0  # Default unique views is set to 0


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

    def __init__(self, course_id, span_range, modname):
        """Instantiate the mixin for course daily indicator."""
        super().__init__(
            object_id=course_id,
            span_range=span_range,
        )
        self.modname = modname

    def get_lrs_query(self):
        """Construct the LRS query for statements whose object is the course.

        WARNING: this method is used only for key cache computing as the LRS
        query requires to look for statements which object is related to the course.
        """
        return LRSStatementsQuery(activity=self.course_id, until=self.until)

    @abstractmethod
    def get_activity_class(self):
        """Return the dataclass for activity views."""
        pass

    @abstractmethod
    def get_views_indicator_class(self):
        """Return the views indicator class."""
        pass

    async def fetch_activities(self):
        """Fetch activities related to the course from the Experience Index."""
        activities = []

        xi = ExperienceIndex(url=moodle_plugin_settings.BASE_XI_URL)
        experience = await xi.experience.get(object_id=self.object_id)
        if experience is None:
            raise ExperienceIndexException(
                f"Unknown course {self.object_id}. It should be indexed first!"
            )
        if not experience.relations_target:
            raise ExperienceIndexException(
                f"No content indexed for course {self.object_id}"
            )

        for source in experience.relations_target:
            content = await xi.experience.get(object_id=source.source_id)
            if content is None:
                raise ExperienceIndexException(
                    f"Cannot find content with id {source.source_id}"
                    f" for course {self.object_id}"
                )
            if content.technical_datatypes[0] in self.modname or self.modname is None:
                activities.append(
                    self.get_activity_class()(
                        modname=content.technical_datatypes[0], id=content.iri
                    )
                )

        return activities

    async def compute(self) -> List:
        """Compute and return the views of course-related activities."""
        activities = await self.fetch_activities()
        views_class = self.get_views_indicator_class()

        # Compute views for each activity and update the views field value if
        # views statements are fetched from the LRS
        for activity in activities:
            views = await views_class(
                object_id=activity.id, span_range=self.span_range
            ).get_or_compute()
            activity.views = views

        return activities


class CourseDailyViews(CourseDailyMixin):
    """Class to compute daily views for course-related activities."""

    def get_activity_class(self):
        """Return the ActivityViews class for standard views."""
        return ActivityViews

    def get_views_indicator_class(self):
        """Return the DailyViews class for calculating views."""
        return DailyViews


class CourseDailyUniqueViews(CourseDailyMixin):
    """Class to compute daily unique views for course-related activities."""

    def get_activity_class(self):
        """Return the ActivityUniqueViews class for unique views."""
        return ActivityUniqueViews

    def get_views_indicator_class(self):
        """Return the DailyUniqueViews class for calculating unique views."""
        return DailyUniqueViews
