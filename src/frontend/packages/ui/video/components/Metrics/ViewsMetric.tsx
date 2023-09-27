import React, { useMemo } from "react";
import useFilters from "../../hooks/useFilters";
import { useVideosViews } from "../../api/getVideoViews";
import { sumViews } from "../../utils";
import { Metric, MetricProps } from "../../../components/Metrics";

export interface ViewsMetricProps extends MetricProps {
  unique?: boolean;
  complete?: boolean;
}

/**
 * ViewsMetric Component
 *
 * A React functional component that displays a metric related to selected videos' views.
 * The metric can be parametrized based on various options such as uniqueness and completeness.
 *
 * @component
 * @param {ViewsMetricProps} props - The props for the ViewsMetric component.
 * @param {string} props.tooltip - The tooltip text for the metric.
 * @param {string} props.title - The title of the metric.
 * @param {boolean} props.unique - Indicates whether to consider unique views.
 * @param {boolean} props.complete - Indicates whether to consider complete views.
 * @returns {JSX.Element} The JSX for the ViewsMetric component.
 */
export const ViewsMetric: React.FC<ViewsMetricProps> = ({
  tooltip,
  title,
  unique,
  complete,
}) => {
  const {
    date: [since, until],
    videoIds,
  } = useFilters();

  const { videoViews, isFetching } = useVideosViews(videoIds, {
    since,
    until,
    unique,
    complete,
  });
  const total = useMemo(() => sumViews(videoViews), [videoViews]);

  return (
    <Metric
      title={title}
      tooltip={tooltip}
      value={total}
      isFetching={isFetching}
    />
  );
};
