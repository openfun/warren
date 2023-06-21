from typing import List, Dict

import pandas as pd

from ralph.backends.http.lrs import LRSQuery, BaseHTTP
from ralph.models.xapi.concepts.constants.video import RESULT_EXTENSION_TIME
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from warren_video.base import BaseIndicator
from warren_video.conf import settings as video_plugin_settings


class DailyVideoViews(BaseIndicator):

    client: BaseHTTP
    activity: str
    since: str
    until: str

    def __init__(self, client: BaseHTTP, activity: str,  since: str, until: str):
        """
        Instantiate the indicator with its parameters. `since` and `until` are dates or timestamps that must be
        in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss.SSSZ")

        Args:
            client: The LRS backend from which the query is to be issued
            activity: The UUID of the video on which to compute the metric
            since: The beginning of the date range on which to compute the indicator
            until: The end of the date range on which to compute the indicator
        """
        self.client = client
        self.activity = activity
        self.since = since
        self.until = until

    def get_query(self) -> LRSQuery:
        query = {
            "verb": PlayedVerb().id,
            "activity": self.activity,
            "since": self.since,
            "until": self.until,
        }
        return LRSQuery(query=query)

    def get_statements(self) -> List:
        filter_query = self.get_query()
        statements = list(self.client.read(target=self.client.statements_endpoint, query=filter_query))
        return statements

    def compute(self) -> Dict:
        """
        Queries the LRS backend and performs adequate filtering and aggregation to return
        the number of video views per day
        """
        raw_statements = self.get_statements()
        if not raw_statements:
            return {"total_views": 0, "views_count_by_date": {}}
        flattened = pd.json_normalize(raw_statements)
        # Filter out events whose verb is not "played"
        filtered_verb = flattened[flattened['verb.id'] == PlayedVerb().id]
        # Filter out videos played less than the configured time
        filtered_view_duration = filtered_verb[filtered_verb[f'result.extensions.{RESULT_EXTENSION_TIME}']
                                               < video_plugin_settings.VIEWS_COUNT_TIME_THRESHOLD].copy()
        # Transform timestamp column into a day
        filtered_view_duration['timestamp'] = pd.to_datetime(filtered_view_duration['timestamp'])
        filtered_view_duration['date'] = filtered_view_duration['timestamp'].dt.strftime('%Y-%m-%d')

        # Group by day and calculate sum of events per day
        count_by_date = filtered_view_duration.groupby('date')\
            .count()\
            .reset_index()\
            .rename(columns={'id': 'count'})\
            .loc[:, ['date', 'count']]
        # Calculate the total number of events
        total_count = len(filtered_view_duration.index)

        return {"total_views": total_count, "views_count_by_date": count_by_date.to_dict('records')}
