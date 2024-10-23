import React, { useMemo } from "react";
import dayjs from "dayjs";
import { useIsFetching } from "@tanstack/react-query";
import {
  formatDates,
  Metric,
  MetricCondensed,
  MetricProps,
  useFilters,
} from "@openfun/warren-core";
import { useDocumentFilters } from "../../hooks";
import { DEFAULT_BASE_QUERY_KEY, useDocumentDownloads } from "../../api";
import { sumDownloads } from "../../utils";

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
  return formatDates([
    dayjs(since).subtract(periodDuration, "day"),
    dayjs(since).subtract(1, "day"),
  ]);
};

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
  } = useFilters();
  const { documents } = useDocumentFilters();

  const params = { unique };

  const { documentDownloads, isFetching } = useDocumentDownloads(documents, {
    since,
    until,
    ...params,
  });
  const total = useMemo(
    () => sumDownloads(documentDownloads),
    [documentDownloads],
  );

  const [comparisonSince, comparisonUntil] = useMemo(
    () => previousPeriod(since, until),
    [since, until],
  );

  // Wait until the before last document downloads has resolved
  const isComparisonWaiting = useMemo(
    () => !documentDownloads.length || fetchingCount > 1,
    [isFetching, documentDownloads],
  );

  const {
    documentDownloads: comparisonData,
    isFetching: isComparisonFetching,
  } = useDocumentDownloads(
    documents,
    {
      since: comparisonSince,
      until: comparisonUntil,
      ...params,
    },
    isComparisonWaiting,
    DEFAULT_BASE_QUERY_KEY + "Comparison",
  );
  const comparison = useMemo(
    () => sumDownloads(comparisonData),
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
