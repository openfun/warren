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
import { DEFAULT_BASE_QUERY_KEY, useResourceViews } from "../../api";

export interface ViewsMetricProps extends Omit<MetricProps, "metric"> {
  unique?: boolean;
  complete?: boolean;
  condensed?: boolean;
}

/**
 * ViewsMetric Component
 *
 * A React functional component that displays a metric related to selected resources' views.
 * The metric can be parametrized based on various options such as uniqueness and completeness.
 * It also includes a comparison with the previous period of the same length.
 *
 * @component
 * @param {ViewsMetricProps} props - The props for the ViewsMetric component.
 * @param {string} props.tooltip - The tooltip text for the metric.
 * @param {string} props.title - The title of the metric.
 * @param {boolean} props.unique - Indicates whether to consider unique views.
 * @param {boolean} props.condensed - Indicates whether to render condensed metric.
 * @returns {JSX.Element} The JSX for the ViewsMetric component.
 */
export const ViewsMetric: React.FC<ViewsMetricProps> = ({
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

  const { resourceMetrics, isFetching } = useResourceViews(resources, {
    since,
    until,
    ...params,
  });
  const total = useMemo(() => sumMetrics(resourceMetrics), [resourceMetrics]);

  const [comparisonSince, comparisonUntil] = useMemo(
    () => getPreviousPeriod(since, until),
    [since, until],
  );

  // Wait until the before last resource views has resolved
  const isComparisonWaiting = useMemo(
    () => !resourceMetrics.length || fetchingCount > 1,
    [isFetching, resourceMetrics],
  );

  const { resourceMetrics: comparisonData, isFetching: isComparisonFetching } =
    useResourceViews(
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
