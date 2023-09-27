import React from "react";
import classNames from "classnames";
import { Card, CardProps } from "../Card";

export interface MetricProps extends Omit<CardProps, "children"> {
  value: number;
  isFetching?: boolean;
}

/**
 * A reusable component for displaying a metric with a title, value, and optional tooltip.
 *
 * @param {MetricProps} props - The component's props.
 * @returns {JSX.Element} The JSX for the Metric component.
 */
export const Metric: React.FC<MetricProps> = ({
  title,
  tooltip,
  value,
  isFetching,
}) => (
  <Card title={title} tooltip={tooltip}>
    <h4
      className={classNames(["c__metric__value"], {
        "c__metric__value--fetching": isFetching,
      })}
    >
      {value}
    </h4>
  </Card>
);
