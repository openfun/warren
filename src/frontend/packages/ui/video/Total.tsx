import { useState, useContext } from "react";
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

type DateRange = {
  since: Date;
  until: Date;
};

type Total = {
  videoIds: Array<string>;
};

type VideoViewStore = {
  [key: string]: VideoViewsResponse;
};

export const Total = ({ videoIds }: Total) => {
  const [videoViewStore, setVideoViewStore] = useState<VideoViewStore>({});

  const { since, until } = useContext(DateContext);

  const results = useQueries({
    queries: videoIds.map((videoId) => {
      return {
        queryKey: [`videoViews-${videoId}`, since, until],
        queryFn: () => getVideoViews(videoId, since, until),
        onSuccess: (data: VideoViewsResponse) => {
          // console.log(data);
          videoViewStore[videoId] = data;
          return data;
        },
      };
    }),
  });

  function calculateTotal(videoViews: VideoViewStore) {
    return Object.entries(videoViews).reduce(
      (acc: number, [vid, views]) => acc + views.total,
      0
    );
  }

  if (results.some((result) => result.isLoading))
    return <span>Loading...</span>;

  return (
    <>
      <h1>Total Views</h1>
      <h2>{calculateTotal(videoViewStore)} views in total</h2>
      {Object.entries(videoViewStore).map(([vid, views]) => (
        <p key={vid}>
          {views.total} total views for {vid}
        </p>
      ))}
    </>
  );
};
