import React, { useMemo } from "react";
import dayjs from "dayjs";
import { useIsFetching } from "@tanstack/react-query";
import useFilters from "../../hooks/useFilters";
import {
  DEFAULT_BASE_QUERY_KEY,
  useVideosViews,
} from "../../api/getVideoViews";
import { formatDates, sumViews } from "../../utils";
import {
  Metric,
  MetricCondensed,
  MetricProps,
} from "../../../components/Metrics";

/**
 * Calculate the previous time period based on the provided since and until dates.
 *
 * This function calculates the start and end dates of the previous time period relative to the given 'since' and 'until' dates.
 * It computes the duration of the selected period and calculates the previous period's start and end dates accordingly.
 *
 * @param {string} since - The start date of the current period.
 * @param {string} until - The end date of the current period.
 * @returns {string[]} An array of two ISO date strings representing the start and end dates of the previous time period.
 */
const previousPeriod = (since: string, until: string) => {
  const periodDuration = dayjs(until).diff(since, "day") + 1;
  return formatDates(
    [periodDuration, 1].map((offset) => dayjs(since).subtract(offset, "day")),
  );
};

export interface ViewsMetricProps extends Omit<MetricProps, "metric"> {
  unique?: boolean;
  complete?: boolean;
  condensed?: boolean;
}

/**
 * ViewsMetric Component
 *
 * A React functional component that displays a metric related to selected videos' views.
 * The metric can be parametrized based on various options such as uniqueness and completeness.
 * It also includes a comparison with the previous period of the same length.
 *
 * @component
 * @param {ViewsMetricProps} props - The props for the ViewsMetric component.
 * @param {string} props.tooltip - The tooltip text for the metric.
 * @param {string} props.title - The title of the metric.
 * @param {boolean} props.unique - Indicates whether to consider unique views.
 * @param {boolean} props.complete - Indicates whether to consider complete views.
 * @param {boolean} props.condensed - Indicates whether to render condensed metric.
 * @returns {JSX.Element} The JSX for the ViewsMetric component.
 */
export const ViewsMetric: React.FC<ViewsMetricProps> = ({
  tooltip,
  title,
  unique,
  complete,
  condensed,
}) => {
  const fetchingCount = useIsFetching({ queryKey: [DEFAULT_BASE_QUERY_KEY] });
  const {
    date: [since, until],
    videos,
  } = useFilters();

  const params = { unique, complete };

  const { videoViews, isFetching } = useVideosViews(videos, {
    since,
    until,
    ...params,
  });
  const total = useMemo(() => sumViews(videoViews), [videoViews]);

  const [comparisonSince, comparisonUntil] = useMemo(
    () => previousPeriod(since, until),
    [since, until],
  );

  // Wait until the before last video views has resolved
  const isComparisonWaiting = useMemo(
    () => !videoViews.length || fetchingCount > 1,
    [isFetching, videoViews],
  );

  const { videoViews: comparisonData, isFetching: isComparisonFetching } =
    useVideosViews(
      videos,
      {
        since: comparisonSince,
        until: comparisonUntil,
        ...params,
      },
      isComparisonWaiting,
      DEFAULT_BASE_QUERY_KEY + "Comparison",
    );
  const comparison = useMemo(() => sumViews(comparisonData), [comparisonData]);

  const data = {
    title,
    tooltip,
    metric: { value: total, isFetching },
    comparison: {
      value: comparison,
      isFetching: isComparisonFetching || isComparisonWaiting,
    },
  };

  if (condensed) {
    return <MetricCondensed {...data} />;
  }

  return <Metric {...data} />;
};
