import React, { useState, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import axios from "axios";

import cloneDeep from "lodash.clonedeep";

type DailyViewsResponseItem = {
  day: string;
  views: number;
};

type DailyViewsProps = {
  videoId: string;
};

export const DailyViews = ({ videoId }: DailyViewsProps) => {
  const baseOption: EChartsOption = {
    title: { text: `Daily views for video: ${videoId}` },
    grid: { top: 80, right: 8, bottom: 100, left: 36 },
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
    },
    series: [
      {
        data: [],
        type: "bar",
        smooth: true,
      },
    ],
    tooltip: {
      trigger: "axis",
    },
  };
  const [option, setOption] = useState(baseOption);
  const { isLoading, error, data, isFetching } = useQuery({
    queryKey: [`videoViews-${videoId}`],
    queryFn: () =>
      axios
        .get(
          `${process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/video/${videoId}/views`
        )
        .then((res) => res.data),
    onSuccess: (data) => {
      const newOption = cloneDeep(option);
      const daily_views: Array<DailyViewsResponseItem> = data.daily_views;
      newOption.xAxis.data = daily_views.map((d) => d.day);
      newOption.series[0].data = daily_views.map((d) => d.views);
      setOption(newOption);
      return data;
    },
  });

  if (isLoading) return <span>Loading...</span>;

  if (error instanceof Error)
    return <span>An error has occurred: {error.message}</span>;

  return <ReactECharts option={option} />;
};
