import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";

import cloneDeep from "lodash.clonedeep";
import useFilters from "../hooks/useFilters";
import { VideoViewsResponse } from "./types";
import { useVideosViews } from "./api/getVideoViews";

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
      interval: 0,
    },
    axisLabel: {
      interval: 0,
      rotate: 45,
      height: 200,
    },
  },
  yAxis: {
    type: "value",
    name: "# views",
    min: 0,
    max: 100,
  },
  series: [],
  tooltip: {
    trigger: "axis",
  },
  textStyle: {
    fontFamily: "Roboto, sans-serif",
  },
};

export const DailyViews: React.FC = () => {
  const {
    date: [since, until],
    videoIds,
  } = useFilters();

  const validData = useVideosViews({ videoIds, since, until });

  const parseSeries = (item: VideoViewsResponse): Series => ({
    id: item?.id,
    name: item.id.slice(-5) || "",
    data: item.counts.map((day) => day.count) || [],
    type: "line",
    smooth: 0.2,
    symbol: "none",
    emphasis: {
      focus: "series",
    },
  });

  const parseXAxis = (item: VideoViewsResponse): Array<string> =>
    item.counts.map((day) => day.date) || [];

  const formattedOption = useMemo(() => {
    if (!validData.length) {
      return baseOption;
    }
    const newOption = cloneDeep(baseOption);
    // todo - ongoing discussion in the team, we assume all requests share the same xAxis.
    newOption.xAxis.data = parseXAxis(validData[0]);
    newOption.series = validData.map((d) => parseSeries(d));
    return newOption;
  }, [validData]);

  return (
    <>
      <div className="chart-title">Video: daily views</div>
      <ReactECharts
        option={formattedOption}
        notMerge={true} // todo - update it with replaceMerge, an issue is opened.
        style={{ height: 500 }}
      />
    </>
  );
};
