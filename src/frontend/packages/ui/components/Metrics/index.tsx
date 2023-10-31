import React from "react";
import classNames from "classnames";
import { Card, CardProps } from "../Card";
import { Comparison } from "../Comparison";
import { Tooltip } from "../Tooltip";

export type ValueWithFetchState = {
  value: number;
  isFetching?: boolean;
};

export interface MetricProps extends Omit<CardProps, "children"> {
  metric: ValueWithFetchState;
  comparison?: ValueWithFetchState;
}

/**
 * A reusable component for displaying a metric with a title, value, optional tooltip,
 * and an optional comparison metric, rendered in a card.
 *
 * @param {MetricProps} props - The component's props.
 * @param {string} props.title - The title of the metric.
 * @param {string} props.tooltip - An optional tooltip for the metric.
 * @param {ValueWithFetchState} props.metric - The main metric data, including a numeric value and an optional fetching state.
 * @param {ValueWithFetchState} props.comparison - An optional comparison metric data, also including a numeric value and an optional fetching state.
 * @returns {JSX.Element} The JSX for the Metric component.
 */
// TODO - refactor the component's API.
export const Metric: React.FC<MetricProps> = (props) => (
  <Card title={props.title} tooltip={props.tooltip}>
    <h4
      className={classNames(["c__metric__value"], {
        "c__metric__value--fetching": props.metric.isFetching,
      })}
    >
      {props.metric.value}
    </h4>
    {props.comparison !== undefined && <Comparison {...props} />}
  </Card>
);

/**
 * A reusable component for displaying a metric with a title, value, optional tooltip,
 * and an optional comparison metric, rendered in a condensed manner.
 *
 * @param {MetricProps} props - The component's props.
 * @param {string} props.title - The title of the metric.
 * @param {string} props.tooltip - An optional tooltip for the metric.
 * @param {ValueWithFetchState} props.metric - The main metric data, including a numeric value and an optional fetching state.
 * @param {ValueWithFetchState} props.comparison - An optional comparison metric data, also including a numeric value and an optional fetching state.
 * @returns {JSX.Element} The JSX for the Metric component.
 */
export const MetricCondensed: React.FC<MetricProps> = (props) => (
  <div className="c__metric-condensed">
    <div className="c__metric-condensed__title__container">
      <span className="c__metric-condensed__title">{props.title}</span>
      {props.tooltip && <Tooltip text={props.tooltip} />}
    </div>
    <span className="c__metric-condensed__value">{props.metric.value}</span>
    {props.comparison !== undefined && <Comparison {...props} size="small" />}
  </div>
);
