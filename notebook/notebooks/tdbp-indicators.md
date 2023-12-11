---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.16.0
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

# TdBP indicators computation

<!-- #region -->
In a `venv`:

1. Install necessary local packages for your machine

```bash
pip install ralph-malph[backend-lrs,backend-es,lrs,cli]==3.8.0 more_itertools httpx
```
2. Push statements in Elasticsearch backend used for LRS 
```bash
gunzip -c data-avignon.json.gz | ralph push -b es --es-hosts http://localhost:9200
```

Open a terminal in the lab and install the following packages: 

```bash
pip install ralph-malph[backend-lrs,backend-es,lrs,cli]==3.8.0 more_itertools httpx pandas tabulate seaborn
```
<!-- #endregion -->

```python
# Package imports

import pandas as pd

from ralph.backends.http.lrs import LRSHTTP, LRSQuery
from ralph.conf import LRSHeaders
from datetime import timedelta, datetime, timezone
from tabulate import tabulate
from enum import Enum
from typing import Literal
from IPython.display import display
```

```python
# Constants


class Activities(Enum):
    """Activities identifiers."""

    ASSIGNMENT_SUBMITTED = "\\mod_assign\\event\\assessable_submitted"
    ASSIGNMENT_GRADED = "\\mod_assign\\event\\submission_graded"
    FEEDBACK = "\\mod_feedback\\event\\response_submitted"
    FORUM_DISCUSSION_CREATED = "\\mod_forum\\event\\discussion_created"
    FORUM_POST_CREATED = "\\mod_forum\\event\\post_created"
    TEST = "\\mod_quiz\\event\\attempt_submitted"
    SCORM_PACKAGE_LAUNCHED = "\mod_scorm\event\sco_launched"
    SCORM_PACKAGE_RAW_SUBMITTED = "\mod_scorm\event\scoreraw_submitted"
    SCORM_PACKAGE_STATUS_SUBMITTED = "\mod_scorm\event\status_submitted"


class Ressources(Enum):
    """Ressources identifiers."""

    BOOK = "\\mod_book\\event\\chapter_viewed"
    CHAT = "\mod_chat\event\course_module_viewed"
    DATABASE = "\\mod_data\\event\\course_module_viewed"
    FOLDER = "\\mod_folder\\event\\course_module_viewed"
    FORUM = "\\mod_forum\\event\\discussion_viewed"
    GLOSSARY = "\\mod_glossary\\event\\course_module_viewed"
    IMS_CONTENT_PACKAGE = "\\mod_imscp\\event\\course_module_viewed"
    EXTERNAL_TOOL = "\\mod_lti\\event\\course_module_viewed"
    PAGE = "\\mod_page\\event\\course_module_viewed"
    URL = "\\mod_url\\event\\course_module_viewed"
    WIKI = "\\mod_wiki\\event\\course_module_viewed"


event_name = (
    "context.extensions.http://lrs.learninglocker.net/define/extensions/info.event_name"
)
```

```python
# Initiate LRS client

lrs_client = LRSHTTP(
    base_url="http://ralph:8200",
    username="ralph",
    password="secret",
    headers=LRSHeaders(
        X_EXPERIENCE_API_VERSION="1.0.3", CONTENT_TYPE="application/json"
    ),
)
```

```python
# Extract ressources-related statements

ressources_statements = raw_statements[
    raw_statements[event_name].isin([ressource.value for ressource in Ressources])
]

# Get the first action in the course

# TODO first_action with lrs_query
```

```python
def compute_active_actions(
    action_type: str, date: datetime = None, window_size: int = 15
):
    # Set default date
    if date is None:
        date = datetime.now()

    # Parse datetime to datestring for LRS query
    until = date.strptime("")
    active_actions = []
    dynamic_cohort = []

    while len(active_actions) < 6:
        since = until + pd.offsets.Day(-window_size)
        # Query the LRS
        lrs_query = lrs_client.read(
            target="/xAPI/statements/",
            query=LRSQuery(
                query={
                    "until": until,
                    "since": since,
                }
            ),
        )

        if lrs_query is None:
            # Search on the window_size days before
            until = since + pd.offsets.Day(-window_size)
        else:
            raw_statements = pd.json_normalize(lrs_query)

            # Extract actions_type related statements only
            statements = raw_statements[
                raw_statements[event_name].isin(
                    [activity.value for activity in Activities]
                )
            ]

            statements["timestamp"] = pd.to_datetime(
                statements["timestamp"], format="ISO8601"
            )

            # Count active unique actors in the window
            cohort = pd.unique(window_statements["actor.account.name"])
            dynamic_cohort += cohort

            # Loop on actions
            actions = (
                window_statements.groupby([event_name, "object.definition.name.en"])[
                    "actor.account.name"
                ]
                .count()
                .reset_index()
            )

            # Find active actions on the current window
            for idx in actions.index:
                identifier = actions.iloc[idx]["object.definition.name.en"]
                action = actions.iloc[idx][event_name]
                action_cohort = actions.iloc[idx]["actor.account.name"]

                if 0.1 * len(dynamic_cohort) <= action_cohort and action_cohort >= 3:
                    activation_date = min(
                        statements.loc[
                            (statements[event_name] == action)
                            & (statements["object.definition.name.en"] == identifier)
                        ]["timestamp"]
                    )
                    # Increment active actions stack
                    active_actions.append(
                        [action, identifier, action_cohort, activation_date]
                    )

            window_start = pd.Timestamp(min(statements["timestamp"]))
            # Check if the first action stored in the LRS has been reached
            if window_start == first_action:
                return active_actions, dynamic_cohort, window_start

    return active_actions, dynamic_cohort, window_start
```

```python
compute_active_actions(action_type=None, date=datetime.now())

# TODO check requirements for floating window
```
