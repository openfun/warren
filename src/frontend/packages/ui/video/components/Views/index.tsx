import React, { useMemo, useState } from "react";
import type { EChartsOption } from "echarts-for-react";

import cloneDeep from "lodash.clonedeep";
import ReactECharts from "echarts-for-react";
import classNames from "classnames";
import dayjs from "dayjs";
import { Button } from "@openfun/cunningham-react";
import { VideoViewsResponse } from "../../types";
import { useVideosViews } from "../../api/getVideoViews";
import useFilters from "../../hooks/useFilters";
import { Card } from "../../../components/Card";
import { ViewsMetric, ViewsMetricProps } from "../Metrics";
import { VIDEOS } from "../Filters";

type Series = {
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
 * A React component for displaying daily views of selected videos within a specified date range.
 *
 * This represents an initial, simple implementation of the views plots, where all videos are presented
 * on a single plot using a daily time granularity. Metric tabs at the top offer a concise summary
 * of all views metrics, and also allow users to select which data to plot.
 *
 * @returns {JSX.Element} The JSX for the DailyViews component.
 */
export const DailyViews: React.FC = () => {
  const {
    date: [since, until],
    videos,
  } = useFilters();

  const [isStacked, setIsStacked] = useState(false);

  const metrics: Array<ViewsMetricProps> = useMemo(() => {
    return [
      {
        title: "Views",
      },
      {
        title: "Viewers",
        unique: true,
      },
      {
        title: "Complete views",
        tooltip:
          "View with a watch time that exceeds the video's completion threshold.",
        complete: true,
      },
      {
        title: "Complete viewers",
        tooltip:
          "Viewer who has watched a video at least once and has a total watch time exceeding the video's completion threshold.",
        unique: true,
        complete: true,
      },
    ];
  }, []);
  const [selectedMetric, setSelectedMetric] = useState(metrics[0]);

  const { videoViews: selectedData } = useVideosViews(videos, {
    since,
    until,
    ...selectedMetric,
  });

  // Convert API response to an EChart series.
  const parseSeries = (item: VideoViewsResponse): Series => ({
    id: item?.id,
    name: VIDEOS.find((video) => video.id === item.id)?.title || "",
    data: item.counts.map((day) => day.count) || [],
    type: "line",
    smooth: 0.2,
    symbol: "none",
    emphasis: {
      focus: "series",
    },
    ...(isStacked && { stack: "Total", areaStyle: {} }),
  });

  const parseXAxis = (item: VideoViewsResponse): Array<string> =>
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
              <ViewsMetric {...metric} condensed />
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
