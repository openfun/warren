import { useState, useContext, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts-for-react";
import { useQueries } from "@tanstack/react-query";
import { getVideoViews } from "./fetchVideoViews";

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

const generateBaseOption: () => EChartsOption = () => ({
  grid: { top: 80, right: 8, bottom: 100, left: 50 },
  xAxis: {
    type: 'category',
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
    type: 'value',
    name: '# views',
  },
  series: [],
  tooltip: {
    trigger: 'axis',
  },
  textStyle: {
    fontFamily: 'Roboto, sans-serif',
  },
});

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
      return {
        queryKey: [`videoViews-${videoId}`, since, until],
        queryFn: () => getVideoViews(videoId, since, until),
        onSuccess: (data: VideoViewsResponse) => {
          setVideoViewStore((prev) => ({ ...prev, [videoId]: data.daily_views }));
          return data;
        },
      };
    }),
  });

  const chartOption = useMemo(() => {
    const baseOption = generateBaseOption();
    const option = { ...baseOption, xAxis: { ...baseOption.xAxis, data: [] }, series: [] };

    Object.entries(videoViewStore).forEach(([videoId, daily_views]) => {
      option.xAxis.data = daily_views.map((d) => d.day);
      option.series.push({
        name: videoId,
        data: daily_views.map((d) => d.views),
        type: 'line',
        smooth: 0.2,
        symbol: 'none',
        areaStyle: {},
        stack: 'Total',
        emphasis: {
          focus: 'series',
        },
      });
    });

    return option;
  }, [videoViewStore]);


  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Daily Views</h1>
      <div className="chart-title">Video: daily views</div>
      <ReactECharts
        option={chartOption}
        style={{ height: 500 }}
      />
    </>
  );
};
