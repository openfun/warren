""""Warren video indicators."""

from typing import TYPE_CHECKING, List

import pandas as pd
from ralph.backends.lrs.base import LRSStatementsQuery
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from warren.indicators import BaseDailyEvent, DailyEvent, DailyUniqueEvent
from warren.xi.client import ExperienceIndex
from warren.xi.exceptions import ExperienceIndexException

from .conf import settings as moodle_plugin_settings

if TYPE_CHECKING:
    _Base = BaseDailyEvent
else:
    _Base = object


class DailyViewsMixin(_Base):
    """Daily Views mixin.

    Calculate the total and daily counts of views.
    """

    def __init__(self, span_range, object_id, activities):
        super().__init__(span_range=span_range, object_id=object_id)
        self.activities = activities

    def filter_statements(self, statements: pd.DataFrame) -> pd.DataFrame:
        """Filter view statements based on additional conditions.

        This method filters the view statements inherited from the base indicator.
        In addition to the base filtering, view statements are further filtered
        based on their duration to match a minimum viewing threshold.
        """
        statements = super().filter_statements(statements)

        # FIXME
        def filter_view_duration(row):
            return (
                row[f"result.extensions.{RESULT_EXTENSION_TIME}"]
                <= moodle_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD
            )

        return statements[statements.apply(filter_view_duration, axis=1)]

    async def get_course_activities(self) -> List[str]:
        """Return activities related to course read from Experience Index."""
        relations = []

        xi = ExperienceIndex(url=moodle_plugin_settings.BASE_XI_URL)
        # Get the course given its experience UUID
        experience = await xi.experience.get(object_id=self.course_id)
        if experience is None:
            raise ExperienceIndexException(
                f"Unknown course {self.course_id}. It should be indexed first!"
            )
        if not experience.relations_target:
            raise ExperienceIndexException(
                f"No content indexed for course {self.course_id}"
            )

        for source in experience.relations_target:
            # Iterate over Moodle activities related to the course
            content = await xi.experience.get(object_id=source.source_id)
            if content is None:
                raise ExperienceIndexException(
                    f"Cannot find content with id {source.source_id} for "
                    f"course {self.course_id}"
                )
            # Filter only on activity types matching required types from API
            elif content.technical_datatypes[0] in self.activities:
                relations.append(content.iri)
            else:
                continue

        return relations

    def get_lrs_query(self):
        """Construct the LRS query for statements whose object is the course.

        WARNING: this method is used only for key cache computing as the LRS
        query requires to look for statements which object is related to the course.
        """
        return LRSStatementsQuery(
            activity=self.course_id,
            verb=self.verb_id,
            until=self.until,
            since=self.since,
        )

    def _get_lrs_query_for_activity(self, activity):
        """Return LRS query for a course-related activity."""
        return LRSStatementsQuery(
            activity=activity, verb=self.verb_id, until=self.until, since=self.since
        )


class DailyViews(DailyViewsMixin, DailyEvent):
    """Daily Views indicator.

    Calculate the total and daily counts of views.

    Inherit from DailyEvent, which provides functionality for calculating
    indicators based on different xAPI verbs.
    """

    # FIXME
    verb_id: str = "http://id.tincanapi.com/verb/viewed"


class DailyUniqueViews(DailyViewsMixin, DailyUniqueEvent):
    """Daily Unique Views indicator.

    Calculate the total, unique and daily counts of views.

    Inherit from DailyUniqueEvent, which provides functionality for calculating
    indicators based on different xAPI verbs and users.
    """

    verb_id: str = "http://id.tincanapi.com/verb/viewed"
