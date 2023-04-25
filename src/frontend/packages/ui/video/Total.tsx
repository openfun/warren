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


type VideoViewStore = {
    [key: string] :  VideoViewsResponse
}


export const Total = ({ videoIds }: Total) => {


  const [videoViewStore, setVideoViewStore] = useState<VideoViewStore>({}) 

  const {since, until} = useContext(DateContext)

  function getVideoViews(videoId: string, since: number , until: number) {
    return axios
      .get(
        `${process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/video/${videoId}/views?since=${since}&until=${until}`
      )
      .then((res) => res.data);
  }

  const results = useQueries({
    queries: 
      videoIds.map((videoId) => {
        return {
          queryKey: [`videoViews-${videoId}`, since, until],
          queryFn: () => getVideoViews(videoId, since, until),
          onSuccess: (data: VideoViewsResponse) => {
            videoViewStore[videoId] = data
            return data;
          },
        };
      }),
  });


  function daysBetween({since, until}: DateRange){
    const millisecondsPerDay = 1000 * 60 * 60 * 24;
    const differenceInMilliseconds = Math.abs(until - since);
    const differenceInDays = differenceInMilliseconds / millisecondsPerDay;
    return Math.round(differenceInDays);
  }

  function calculateTotal(videoViews: VideoViewStore){
    return Object.entries(videoViews).reduce(
      (acc: number, [vid, views]) => acc + views.total ,
      0
      )
  }

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Total Views</h1>
      <h2>{calculateTotal(videoViewStore)} Views</h2>
      <h2>for {videoIds.length} Videos</h2>
      <h2>over {daysBetween({since, until})} days</h2>
      
    </>
  );
};
