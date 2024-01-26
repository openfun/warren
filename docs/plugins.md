# Plugins ecosystem

Warren is extensible by design using a plugins architecture. Warren plugins are
distributed as [Python packages](https://pypi.org/search/?q=warren) for the API
service and indicators, or as
[NPM packages](https://www.npmjs.com/search?q=%40openfun%2Fwarren) for UI
components. This page intends to list known available plugins for Warren (feel
free to open a pull request to add your plugin in this list!).

## Plugins registry

### Indicators (API service)

- [Warren video](https://github.com/openfun/warren/tree/main/src/api/plugins/video)
  :label: : a series of indicators related to Video activity

:label: ― offical plugins (maintained by Warren's core team)

### Dataviz (Front-end / APP service)

- [Warren video](https://github.com/openfun/warren/tree/main/src/frontend/packages/video)
  :label: : a series of ReactJS component to explore Video activity in your
  Dashboards.

:label: ― offical plugins (maintained by Warren's core team)

## Create your own plugin for Warren

### API

To make your plugin auto-magically discoverable by Warren, you should declare
[entry points in your module's package](https://setuptools.pypa.io/en/latest/userguide/entry_point.html).
Two groups of entry points can be declared depending on what your plugin
extends:

- `warren.routers`: add new routers to the core API
- `warren.indicators`: allow to compute indicators from the CLI (see
  `warren indicator` command documentation)

As an example, the Warren Video plugin implements such entry points in its
package definition:

```toml
# pyproject.toml

[project.entry-points."warren.routers"]
video = "warren_video.api:router"

[project.entry-points."warren.indicators"]
daily_views = "warren_video.indicators:DailyViews"
daily_unique_views = "warren_video.indicators:DailyUniqueViews"
daily_completed_views = "warren_video.indicators:DailyCompletedViews"
daily_unique_completed_views = "warren_video.indicators:DailyUniqueCompletedViews"
daily_downloads = "warren_video.indicators:DailyDownloads"
daily_unique_downloads = "warren_video.indicators:DailyUniqueDownloads"
```

You can check that your indicators are properly registered using the following
command:

```bash
warren indicator list
```

If only the `warren_video` plugin is installed, the command output looks like:

```
warren_video.indicators:DailyCompletedViews
warren_video.indicators:DailyDownloads
warren_video.indicators:DailyUniqueCompletedViews
warren_video.indicators:DailyUniqueDownloads
warren_video.indicators:DailyUniqueViews
warren_video.indicators:DailyViews
```

### Front-end

TODO
