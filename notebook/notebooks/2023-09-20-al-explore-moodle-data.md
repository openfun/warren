---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.15.2
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

```python
!pip install itables > /dev/null
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Imports
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
import json
from datetime import datetime

from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.io as pio
from matplotlib import pyplot as plt
from itables import init_notebook_mode, show
```

```python
init_notebook_mode(all_interactive=False)
pio.renderers.default = 'plotly_mimetype+notebook'
```

_______________
### Functions

```python
def percentage_number(condition):
    p = sum(condition) / len(condition)
    print(f'{p:0.02%} ({sum(condition)} over {len(condition)})')
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Load data
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
filename = 'your-filename'
filepath = Path('./data') / filename
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
%%time
# Open file's content
lines = filepath.read_text().splitlines()
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
%%time
# Convert lines to a dataframe
statements_raw = [json.loads(l) for l in lines]
df = pd.json_normalize(statements_raw)
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Columns
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
df.info()
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Statements' id

Ensure statements have distinct ID values.
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
id_counts = df['id'].value_counts()
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
any(id_counts > 1)
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Process list columns

While using `json_normalize` from pandas, we encountered some columns that were not successfully flattened due to their complex nested structure. To handle these columns, we applied manual processing and transformation techniques to ensure data integrity and usability.

<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# Enumerate nested columns containing lists of dictionaries
columns_contain_list = (df.map(type) == list).any()
columns_contain_list = set(columns_contain_list.index[columns_contain_list])

# Print columns' names
print(*columns_contain_list, sep='\n')
```

#### context.contextActivities.other

```python
# Example of a 'context.contextActivities.other' value
example = df['context.contextActivities.other'][
    df['context.contextActivities.other'].notna()
].values[0]

# Pretty print an example value, all items share the same Json format.
# 'id' and 'type' can be extracted.
print(json.dumps(example, indent=4))
```

```python
# Assuming 'context.contextActivities.other' is a list of dictionaries,
#  extract its 'id'
df['context.contextActivities.other.id'] = (
    df['context.contextActivities.other']
    .map(lambda row: row[0]['id'] if isinstance(row, list) else row)
)
```

```python
# Assuming 'context.contextActivities.other' is a list of dictionaries,
#  extract its 'type'
df['context.contextActivities.other.type'] = (
    df['context.contextActivities.other']
    .map(lambda row: row[0]['definition']['type'] if isinstance(row, list) else row)
)
```

#### context.contextActivities.category

It has only two values. The first one is represented only once.

```python
# Only one statement has a different structure; possible outlier
df['context.contextActivities.category'].value_counts()
```

```python
# Value represented only once.
print(json.dumps(df['context.contextActivities.category'][0], indent=4))
```

```python
# Dominant value.
print(json.dumps(df['context.contextActivities.category'][1], indent=4))
```

```python
# Assuming 'context.contextActivities.category' is a list of dictionaries,
#  extract its 'id'
df['context.contextActivities.category.id'] = (
    df['context.contextActivities.category']
    .map(lambda row: row[0]['id'] if isinstance(row, list) else row)
)
```

#### context.contextActivities.parent

```python
# No extractable data; possible outlier
df['context.contextActivities.parent'].value_counts()
```

#### context.contextActivities.grouping

```python
# Count the number of groups within 'context.contextActivities.grouping'
# This column contains different groups: LMS, Course, Resource

(
    df['context.contextActivities.grouping']
    .map(lambda groups: len(groups) if isinstance(groups, list) else 0)
    .value_counts()
)
```

```python
def _extract_name_from_row(row, idx):
    return row[idx]['definition']['name']['en'] if isinstance(row, list) and len(row) > idx else np.nan
```

```python
# Extract first group, LMS
df['context.contextActivities.grouping.lms'] = (
    df['context.contextActivities.grouping']
    .map(lambda row: _extract_name_from_row(row, 0))
)
```

```python
# Extract second group, Course
df['context.contextActivities.grouping.course'] = (
    df['context.contextActivities.grouping']
    .map(lambda row: _extract_name_from_row(row, 1))
)
```

```python
df['context.contextActivities.grouping.course']
```

```python
# Extract third group, Resource
df['context.contextActivities.grouping.resource'] = (
    df['context.contextActivities.grouping']
   .map(lambda row: _extract_name_from_row(row, 2))
)
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Verbs' ID
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# Representation of each xAPI verb
df['verb.id'].value_counts(normalize=True) * 100
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______________
### Timestamp
<!-- #endregion -->

```python
df['datetime'] = pd.to_datetime(df['timestamp'], format='ISO8601', errors='raise', utc=True)
```

```python
# All share the same year, 2021
df['datetime'].dt.year.unique()
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# Start : 2021-08-31
df['datetime'].min()
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# End : 2021-11-29
df['datetime'].max()
```

```python
all_statements = df['datetime'].sort_values().value_counts(sort=False).to_frame().reset_index()
fig = px.line(all_statements, x='datetime', y='count', title='Statements over time')
fig.show()
```

<!-- #region jupyter={"outputs_hidden": false} -->
___________
### Actors
<!-- #endregion -->

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
statement_counts_per_actor = df['actor.account.name'].value_counts()
```

```python
# Number of actors
len(statement_counts_per_actor)
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# 10% of the actors have a single statement
percentage_number(statement_counts_per_actor == 1)
```

```python
# 3/4 of the actors have less than 22 statements
percentage_number(statement_counts_per_actor < 22)
```

```python jupyter={"outputs_hidden": false} pycharm={"name": "#%%\n"}
# 99% of the actors have less than 90 statements
percentage_number(statement_counts_per_actor < 90)
```

```python
# Have a quick look to counts per actors distribution
plt.hist(statement_counts_per_actor.values, range(0,90))
plt.xlabel('# statements per actor')
plt.ylabel('# actors')
_ = plt.title('Counts in [0, 90] Range')
```

```python
# Most of the actors with a single statements are registered statements
df.groupby('actor.account.name').filter(lambda x: len(x) == 1)['verb.id'].value_counts(dropna=False)
```

<!-- #region jupyter={"outputs_hidden": false} -->
_______
### Courses

<!-- #endregion -->

```python
statement_counts_per_course = df['context.contextActivities.grouping.course'].value_counts()
```

```python
# Number of courses
len(statement_counts_per_course)
```

```python
# More than 10% of the courses have a single statement
percentage_number(statement_counts_per_course==1)
```

```python
# 3/4 of the courses have less than 75 statements
percentage_number(statement_counts_per_course < 75)
```

```python
# 99% of the courses have less than 900 statements
percentage_number(statement_counts_per_course < 900)
```

```python
# Have a quick look to counts distribution
plt.hist(statement_counts_per_course.values, range=(0,900), bins=100)
plt.xlabel('# statements per course')
plt.ylabel('# courses')
_ = plt.title('Counts in [0, 900] Range')
```

```python
# Explore manually counts per course
show(statement_counts_per_course)
```

_______
### Course / verb pairs


```python
# Explore manually relationship between courses and verbs
show(pd.crosstab(df['context.contextActivities.grouping.course'], df['verb.id'], dropna=False))
```

```python
# Most of the courses have only viewed statements
# Number of courses that have only viewed statements, over 677 courses
sum(pd.crosstab(df['context.contextActivities.grouping.course'], df['verb.id'], normalize='index')['http://id.tincanapi.com/verb/viewed'] == 1)
```

```python
# Explore manually relationship between courses and viewed verb
# The cross-table is normalized row-wise
# 1 means that 100% of the course's statements are viewed events
show(pd.crosstab(df['context.contextActivities.grouping.course'], df['verb.id'], normalize='index')['http://id.tincanapi.com/verb/viewed'])
```

_______
### Courses and actors


```python
students_count_per_course = df.groupby('context.contextActivities.grouping.course')['actor.name'].nunique()
```

```python
# 22% of the courses have a single student
percentage_number(students_count_per_course == 1)
```

```python
# 75% of the courses have less than 20 students
percentage_number(students_count_per_course < 20)
```

```python
# 99% of the courses have less than 180 students
percentage_number(students_count_per_course < 180)
```

```python
# Have a quick look to counts
fig = px.box(
    students_count_per_course.values,
    title='# statements per course, ignoring outliers over 180'
)
fig.update_yaxes(range=[0,180])
fig.show()
```

```python
# Explore manually students per course
show(students_count_per_course)
```

_______
### Course activity


```python
# Set the course's ID you want to plot
course_id = 'Cours 3141707131501911347'


course_statements = df[
    df['context.contextActivities.grouping.course'] == course_id
]

course_hourly_counts = (
    course_statements.groupby(pd.Grouper(key='datetime', freq='H'))
    ['datetime']
    .count()
    .to_frame()
    .rename({'datetime': 'count'}, axis='columns')
    .reset_index()
)

fig = px.line(course_hourly_counts, x='datetime', y='count', title=f'Statements over time for {course_id}')
fig.show()
```

```python
# Plot how student activity is distributed for the selected course
fig = px.box(
    course_statements['actor.name'].value_counts(),
    y='count',
    title='# statements per actor'
)
fig.show()
```
