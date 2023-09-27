import React, { useMemo } from "react";
import type { EChartsOption } from "echarts-for-react";

import cloneDeep from "lodash.clonedeep";
import { Line } from "../../../components/Plots/Line";
import { VideoViewsResponse } from "../../types";
import { useVideosViews } from "../../api/getVideoViews";
import useFilters from "../../hooks/useFilters";

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

/**
 * A React component for displaying daily views of selected videos within a specified date range.
 *
 * This represents an initial, simple implementation of the views plots, where all videos are presented
 * on a single plot using a daily time granularity. While data is being fetched, a loading spinner is
 * displayed within the plot.
 *
 * @returns {JSX.Element} The JSX for the DailyViews component.
 */
export const DailyViews: React.FC = () => {
  const {
    date: [since, until],
    videoIds,
  } = useFilters();

  const { videoViews, isFetching } = useVideosViews(videoIds, { since, until });

  // Convert API response to an EChart series.
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
    if (!videoViews.length) {
      return baseOption;
    }
    const newOption = cloneDeep(baseOption);
    // We assume all requests share the same xAxis.
    newOption.xAxis.data = parseXAxis(videoViews[0]);
    newOption.series = videoViews.map((d) => parseSeries(d));
    return newOption;
  }, [videoViews]);

  return <Line title="Views" option={formattedOption} isLoading={isFetching} />;
};
