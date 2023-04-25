import React, { useState, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";
import { useQuery, useQueries, useQueryClient } from "@tanstack/react-query";

import axios from "axios";

import cloneDeep from "lodash.clonedeep";

type DailyViewsResponseItem = {
  day: string;
  views: number;
};

type VideoViewsResponse = {
  total: number;
  daily_views: Array<DailyViewsResponseItem>;
};

type DailyViewsProps = {
  videoIds: Array<string>;
  since: Date;
  until: Date;
};

export const DailyViews = ({ videoIds, since_unix_ms, until_unix_ms }: DailyViewsProps) => {
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
    },
    series: [],
    tooltip: {
      trigger: "axis",
    },
    textStyle: {
      fontFamily: "Roboto, sans-serif",
    },
  };

  const [option, setOption] = useState(baseOption);

  const newOption = cloneDeep(option);

  function getVideoViews(videoId: string, since: Date , until: Date) {
    return axios
      .get(
        `${process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/video/${videoId}/views?since=${since_unix_ms}&until=${until_unix_ms}`
      )
      .then((res) => res.data);
  }

  function addOneSeries(
    videoId: string,
    daily_views: Array<DailyViewsResponseItem>
  ) {
    newOption.xAxis.data = daily_views.map((d) => d.day);
    newOption.series.push({
      name: videoId,
      data: daily_views.map((d) => d.views),
      type: "line",
      smooth: 0.2,
      symbol: "none",
      areaStyle: {},
      stack: "Total",
      emphasis: {
        focus: "series",
      },
    });
    setOption(newOption);
  }

  const results = useQueries({
    queries: videoIds.map((videoId) => {
      return {
        queryKey: [`videoViews-${videoId}`],
        queryFn: () => getVideoViews(videoId, since_unix_ms, until_unix_ms),
        onSuccess: (data: VideoViewsResponse) => {
          addOneSeries(videoId, data.daily_views);
          return data;
        },
      };
    }),
  });

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <div className="chart-title">Video: daily views</div>
      <ReactECharts option={option} style={{ height: 500 }} />
    </>
  );
};
