import { useState, useContext, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getVideoViews } from "./fetchVideoViews";

import axios from "axios";

import cloneDeep from "lodash.clonedeep";

import { DateContext } from "../DateContext";

type DailyViewsResponseItem = {
  day: string;
  views: number;
};

type VideoViewsResponse = {
  total: number;
  daily_views: Array<DailyViewsResponseItem>;
};

type DailyViewsAreaGraphProps = {
  videoIds: Array<string>;
};

export const DailyViewsAreaGraph = ({ videoIds }: DailyViewsAreaGraphProps) => {
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
  type videoViewStoreType = {
    [key: string]: Array<DailyViewsResponseItem>;
  };

  const [videoViewStore, setVideoViewStore] = useState<videoViewStoreType>({});

  const newOption = cloneDeep(option);

  const { since, until } = useContext(DateContext);

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

  // # FIXME: Race condition
  // some data are lost if useQueries fetch data before useEffect is triggered
  // even if its unlikely we should not rely on that
  // Use chained queries instead ?
  useEffect(() => {
    newOption.series = [];
    option.series = [];
  }, [videoIds, since, until]);

  const results = useQueries({
    queries: videoIds.map((videoId) => {
      return {
        queryKey: [`videoViews-${videoId}`, since, until],
        queryFn: () => getVideoViews(videoId, since, until),
        onSuccess: (data: VideoViewsResponse) => {
          addOneSeries(videoId, data.daily_views);
          videoViewStore[videoId] = data.daily_views;
          return data;
        },
      };
    }),
  });

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Daily Views</h1>
      <div className="chart-title">Video: daily views</div>
      <ReactECharts option={option} style={{ height: 500 }} />
    </>
  );
};
