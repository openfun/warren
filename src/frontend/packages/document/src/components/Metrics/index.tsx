import React, { useMemo } from "react";
import { useIsFetching } from "@tanstack/react-query";
import {
  Metric,
  MetricCondensed,
  MetricProps,
  getPreviousPeriod,
  useDateFilters,
  useResourceFilters,
  sumMetrics,
} from "@openfun/warren-core";
import { DEFAULT_BASE_QUERY_KEY, useDocumentDownloads } from "../../api";

export interface DownloadsMetricProps extends Omit<MetricProps, "metric"> {
  unique?: boolean;
  condensed?: boolean;
}

/**
 * DownloadsMetric Component
 *
 * A React functional component that displays a metric related to selected documents' downloads.
 * The metric can be parametrized based on various options such as uniqueness.
 * It also includes a comparison with the previous period of the same length.
 *
 * @component
 * @param {DownloadsMetricProps} props - The props for the DownloadsMetric component.
 * @param {string} props.tooltip - The tooltip text for the metric.
 * @param {string} props.title - The title of the metric.
 * @param {boolean} props.unique - Indicates whether to consider unique downloads.
 * @param {boolean} props.complete - Indicates whether to consider complete downloads.
 * @param {boolean} props.condensed - Indicates whether to render condensed metric.
 * @returns {JSX.Element} The JSX for the DownloadsMetric component.
 */
export const DownloadsMetric: React.FC<DownloadsMetricProps> = ({
  tooltip,
  title,
  unique,
  condensed,
}) => {
  const fetchingCount = useIsFetching({ queryKey: [DEFAULT_BASE_QUERY_KEY] });
  const {
    date: [since, until],
  } = useDateFilters();
  const { resources } = useResourceFilters();

  const params = { unique };

  const { resourceMetrics, isFetching } = useDocumentDownloads(resources, {
    since,
    until,
    ...params,
  });
  const total = useMemo(() => sumMetrics(resourceMetrics), [resourceMetrics]);

  const [comparisonSince, comparisonUntil] = useMemo(
    () => getPreviousPeriod(since, until),
    [since, until],
  );

  // Wait until the before last document downloads has resolved
  const isComparisonWaiting = useMemo(
    () => !resourceMetrics.length || fetchingCount > 1,
    [isFetching, resourceMetrics],
  );

  const { resourceMetrics: comparisonData, isFetching: isComparisonFetching } =
    useDocumentDownloads(
      resources,
      {
        since: comparisonSince,
        until: comparisonUntil,
        ...params,
      },
      isComparisonWaiting,
      DEFAULT_BASE_QUERY_KEY + "Comparison",
    );
  const comparison = useMemo(
    () => sumMetrics(comparisonData),
    [comparisonData],
  );

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
