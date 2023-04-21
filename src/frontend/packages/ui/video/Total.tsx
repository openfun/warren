import React, { useState, useEffect, useContext } from "react";
import { useQueries } from "@tanstack/react-query";

import axios from "axios";

import { DateContext } from "../DateContext";

type DailyViewsResponseItem = {
  day: string;
  views: number;
};

type VideoViewsResponse = {
  total: number;
  daily_views: Array<DailyViewsResponseItem>;
};

type DateRange = {
  since: number;
  until: number;
}

type Total = {
  videoIds: Array<string>;
};

type videoViewStoreType = {
    [key: string] :  Array<DailyViewsResponseItem>
}

export const Total = ({ videoIds }: Total) => {


  const [videoViewStore, setVideoViewStore] = useState<videoViewStoreType>({}) 

  const [totalVideoViews, setTotalVideoViews] = useState(0)

  const {since, until} = useContext(DateContext)
  const sinceUnixMs = since
  const untilUnixMs = until

  function getVideoViews(videoId: string, sinceUnixMs: number , untilUnixMs: number) {
    return axios
      .get(
        `${process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/video/${videoId}/views?since=${sinceUnixMs}&until=${untilUnixMs}`
      )
      .then((res) => res.data);
  }

  const results = useQueries({
    queries: 
      videoIds.map((videoId) => {
        return {
          queryKey: [`videoViews-${videoId}`, since, until],
          queryFn: () => getVideoViews(videoId, sinceUnixMs, untilUnixMs),
          onSuccess: (data: VideoViewsResponse) => {
            videoViewStore[videoId] = data.daily_views
            return data;
          },
        };
      }),
  });

  function calculateTotalViewOnDateRange(videoViewStore: videoViewStoreType, videoIds: Array<string>, since: number, until: number) {
    const filtered_videos = Object.entries(videoViewStore).filter( ([vid]) => videoIds.indexOf(vid) >= 0)
    const totalViewOfOneVideo = (daily_views: Array<DailyViewsResponseItem>) => daily_views.reduce( (acc: number, d: DailyViewsResponseItem) => acc + d.views, 0)
    const total_views_of_all_videos = filtered_videos.reduce( 
                                        (acc:number, [vid, daily_views]) =>  acc + totalViewOfOneVideo(daily_views) 
                                          , 0) 
    return total_views_of_all_videos
  }

  function daysBetween({since, until}: DateRange){
    const millisecondsPerDay = 1000 * 60 * 60 * 24;
    const differenceInMilliseconds = Math.abs(until - since);
    const differenceInDays = differenceInMilliseconds / millisecondsPerDay;
    return Math.round(differenceInDays);
  }

  function getDateRange(videoViewStore: videoViewStoreType){
    const videos = Object.entries(videoViewStore)
    if (videos.length > 1){
      const firstVideoDailyViews = videos[0][1]
      const since = firstVideoDailyViews.length > 0 ? 
                      new Date(firstVideoDailyViews[0].day).getTime() 
                      : 0
      const until = firstVideoDailyViews.length > 0 ? 
                      new Date(firstVideoDailyViews[firstVideoDailyViews.length -1].day).getTime() 
                      : 0
      return {since, until}
    } else {
      return {since: 0, until: 0}
    }
  }
  

  // FIXME: race condition ( see ViewsAreaGraph )
  useEffect( () => {
    setTotalVideoViews(0)
  }, [videoIds, sinceUnixMs, untilUnixMs])

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Total Views</h1>
      <h2>{calculateTotalViewOnDateRange(videoViewStore, videoIds, sinceUnixMs, untilUnixMs)} Views</h2>
      <h2>for {videoIds.length} Videos</h2>
      <h2>over {daysBetween(getDateRange(videoViewStore))} days</h2>
      
    </>
  );
};
