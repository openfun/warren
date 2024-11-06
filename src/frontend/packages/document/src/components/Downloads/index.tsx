import React, { useMemo, useState } from "react";
import type { EChartsOption } from "echarts-for-react";

import cloneDeep from "lodash.clonedeep";
import ReactECharts from "echarts-for-react";
import classNames from "classnames";
import dayjs from "dayjs";
import { Button } from "@openfun/cunningham-react";
import {
  Card,
  RESOURCES,
  useDateFilters,
  useResourceFilters,
  ResourceMetricsResponse,
} from "@openfun/warren-core";
import { useDocumentDownloads } from "../../api";
import { DownloadsMetric, DownloadsMetricProps } from "../Metrics";

export type Series = {
  id: string;
  name: string;
  data: number[];
  type: string;
  smooth: number;
  symbol: string;
  emphasis: any;
};

const baseOption: EChartsOption = {
  grid: { top: 80, right: 8, bottom: 100, left: 50 },
  xAxis: {
    type: "category",
    data: [],
    axisTick: {
      alignWithLabel: true,
    },
    axisLabel: {
      rotate: 0,
    },
  },
  yAxis: {
    type: "value",
    min: 0,
  },
  series: [],
  tooltip: {
    trigger: "axis",
  },
  textStyle: {
    fontFamily: "Roboto, sans-serif",
  },
};

/**
 * A React component for displaying daily downloads of selected documents within a specified date range.
 *
 * This represents an initial, simple implementation of the downloads plots, where all documents are presented
 * on a single plot using a daily time granularity. Metric tabs at the top offer a concise summary
 * of all downloads metrics, and also allow users to select which data to plot.
 *
 * @returns {JSX.Element} The JSX for the DailyDownloads component.
 */
export const DailyDownloads: React.FC = () => {
  const {
    date: [since, until],
  } = useDateFilters();
  const { resources } = useResourceFilters();

  const [isStacked, setIsStacked] = useState(false);

  const metrics: Array<DownloadsMetricProps> = useMemo(() => {
    return [
      {
        title: "Downloads",
      },
      {
        title: "Downloaders",
        unique: true,
      },
    ];
  }, []);
  const [selectedMetric, setSelectedMetric] = useState(metrics[0]);

  const { resourceMetrics: selectedData } = useDocumentDownloads(resources, {
    since,
    until,
    ...selectedMetric,
  });

  // Convert API response to an EChart series.
  const parseSeries = (item: ResourceMetricsResponse): Series => ({
    id: item?.id,
    name: RESOURCES.find((document) => document.id === item.id)?.title || "",
    data: item.counts.map((day) => day.count) || [],
    type: "line",
    smooth: 0.2,
    symbol: "none",
    emphasis: {
      focus: "series",
    },
    ...(isStacked && { stack: "Total", areaStyle: {} }),
  });

  const parseXAxis = (item: ResourceMetricsResponse): Array<string> =>
    item.counts.map((day) => dayjs(day.date).format("MM/DD")) || [];

  const formattedOption = useMemo(() => {
    if (!selectedData.length) {
      return baseOption;
    }
    const newOption = cloneDeep(baseOption);
    // We assume all requests share the same xAxis.
    newOption.xAxis.data = parseXAxis(selectedData[0]);
    newOption.series = selectedData.map((d) => parseSeries(d));
    return newOption;
  }, [selectedData]);

  return (
    <Card className="c__metrics-tabs__card">
      <div className="c__plot-header">
        <div className="c__metrics-tabs">
          {metrics.map((metric) => (
            <button
              className={classNames(["c__metrics-tabs__tab"], {
                "c__metrics-tabs__tab--selected": metric === selectedMetric,
              })}
              onClick={() => setSelectedMetric(metric)}
            >
              <DownloadsMetric {...metric} condensed />
            </button>
          ))}
        </div>
        <Button
          className="c__plot-header__controls"
          color={isStacked ? "primary" : "tertiary"}
          onClick={() => setIsStacked(!isStacked)}
          icon={<span className="material-icons">area_chart</span>}
        />
      </div>
      <ReactECharts
        option={formattedOption}
        notMerge={true}
        style={{ height: 500, width: "100%" }}
      />
    </Card>
  );
};
