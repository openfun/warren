---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.14.6
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
!pip install ralph-malph==3.7.0 more_itertools httpx
```

```python
from ralph.backends.http.lrs import LRSQuery
from ralph.models.xapi.concepts.verbs.video import PlayedVerb
from ralph.backends.http import LRSHTTP
from ralph.conf import LRSHeaders
import pandas as pd
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
filter_query = {
        "verb": PlayedVerb().id,
        "activity": "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50",
        "since": "2023-01-01T00:00:00.000Z",
        "until": "2024-01-01T00:00:00.000Z",
    }
```

```python
def query_lrs():
    statements = lrs_client.read(target="/xAPI/statements/", query=LRSQuery(query=filter_query))
    # Convert to a DataFrame because it returns a lazy generator otherwise.
    # The time difference between converting to a list or just printing is negligible IMO
    return pd.DataFrame(statements)

def aggregate(df):
    # Prepare a month column
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.month
    
    # Count the number of events in each month
    event_counts = df['month'].value_counts()

def query_and_aggregate():
    df = query_lrs()
    result = aggregate(df)
    return result
```

```python
import cProfile
cProfile.run('query_and_aggregate()', filename="benchmark-aggregation-ralph-malph-3.7.0.profile")
```
