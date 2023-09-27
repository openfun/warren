import React from "react";
import ReactECharts, { EChartsOption } from "echarts-for-react";
import { Card } from "../../Card";

type LineProps = {
  option: EChartsOption;
  title?: string;
  isLoading?: boolean;
};

/**
 * A React component for displaying line charts using ECharts.
 *
 * @param {LineProps} props - The component's props.
 * @returns {JSX.Element} The JSX for the Line component.
 */
// FIXME - overcome ReactECharts limitations, issue 43 is opened.
export const Line: React.FC<LineProps> = ({ option, title, isLoading }) => (
  <Card title={title}>
    <ReactECharts
      option={option}
      notMerge={true}
      style={{ height: 500 }}
      showLoading={isLoading}
    />
  </Card>
);
