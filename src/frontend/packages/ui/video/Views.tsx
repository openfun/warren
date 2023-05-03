import { useState, useContext, useEffect } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getVideoViews } from "./fetchVideoViews";

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

type DailyViewsProps = {
  videoIds: Array<string>;
};

type videoViewStoreType = {
  [key: string]: Array<DailyViewsResponseItem>;
};

export const DailyViews = ({ videoIds }: DailyViewsProps) => {
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

  const [videoViewStore, setVideoViewStore] = useState<videoViewStoreType>({});

  const { since, until } = useContext(DateContext);

  const results = useQueries({
    queries: videoIds.map((videoId) => {
      console.log("query");
      console.log(
        `${
          process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL
        }/api/v1/video/${videoId}/views?since=${since.toISOString()}&until=${until.toISOString()}`
      );
      console.log(since.toISOString());
      return {
        queryKey: [`videoViews-${videoId}`, since, until],
        queryFn: () => getVideoViews(videoId, since, until),
        onSuccess: (data: VideoViewsResponse) => {
          videoViewStore[videoId] = data.daily_views;
          return data;
        },
      };
    }),
  });

  function dataToEChatsOption(
    videoViews: videoViewStoreType,
    baseOption: EChartsOption
  ) {
    const option = cloneDeep(baseOption);
    Object.entries(videoViews).map(([vid, daily_views]) => {
      option.xAxis.data = daily_views.map((d) => d.day);
      option.series.push({
        name: vid,
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
    });
    return option;
  }

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Daily Views</h1>
      <div className="chart-title">Video: daily views</div>
      {/* <ReactECharts option={option} style={{ height: 500 }} /> */}
      <ReactECharts
        option={dataToEChatsOption(videoViewStore, baseOption)}
        style={{ height: 500 }}
      />
      <h2>{dataToEChatsOption(videoViewStore, baseOption).series.length} </h2>
    </>
  );
};
