import pytest
from datetime import datetime, timedelta

@pytest.fixture
def last_week_views():
    def _last_week_views():
        today = datetime.now().date()
        week_ago = today - timedelta(weeks=1)

        week_views = []
        for i in range(8):
            day = week_ago + timedelta(days=i)
            week_views.append({"day": day.isoformat(), "views": 0})

        return week_views

    return _last_week_views
