import React, { useMemo } from "react";
import classNames from "classnames";
import { MetricProps } from "../Metrics";

const formatPercent = (percent: number) => `${(percent * 100).toFixed(0)}%`;

export interface ComparisonProps
  extends Pick<MetricProps, ["metric", "comparison"]> {
  size?: "medium" | "small";
}

/**
 * A React component for displaying a comparison metric with a dynamic icon and percentage change.
 *
 * This component takes two metrics, 'metric' and 'comparison', and calculates the percentage change between them.
 * It displays an icon and percentage value, with optional fetching state indicators and tooltips.
 *
 * @param {ComparisonProps} props - The component's props.
 * @param {ValueWithFetchState} props.metric - The primary metric data, including a numeric value and an optional fetching state.
 * @param {ValueWithFetchState} props.comparison - The comparison metric data, including a numeric value and an optional fetching state.
 * @returns {JSX.Element} The JSX for the Comparison component.
 */
export const Comparison: React.FC<ComparisonProps> = ({
  metric,
  comparison,
  size = "medium",
}) => {
  const comparisonToNull = useMemo(() => comparison.value === 0, [comparison]);

  const percent = useMemo(
    () =>
      !comparisonToNull && (metric.value - comparison.value) / comparison.value,
    [metric, comparison],
  );

  const isStrictlyNegative = useMemo(() => percent < 0, [percent]);
  const isStrictlyPositive = useMemo(() => percent > 0, [percent]);

  const iconName = useMemo(() => {
    if (percent === 0) {
      return "horizontal_rule";
    }
    return `arrow_${isStrictlyNegative ? "down" : "up"}ward`;
  }, [percent, isStrictlyNegative]);

  return (
    <div
      className={classNames(["c__comparison"], {
        c__comparison__small: size === "small",
        "c__comparison--fetching": comparison.isFetching || metric.isFetching,
        "c__comparison--negative": isStrictlyNegative,
        "c__comparison--positive": isStrictlyPositive,
      })}
    >
      {comparison.isFetching || metric.isFetching || comparisonToNull ? (
        <span className="material-icons">horizontal_rule</span>
      ) : (
        <>
          <span className="material-icons">{iconName}</span>
          <p>{percent ? formatPercent(percent) : ""}</p>
        </>
      )}
    </div>
  );
};
