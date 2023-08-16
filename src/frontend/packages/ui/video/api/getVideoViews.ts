import { useQueries } from "@tanstack/react-query";
import { axios } from "../../libs/axios";
import { VideoViewsResponse } from "../types";

const getVideoViews = async (
  videoId: string,
  since: string,
  until: string,
): Promise<VideoViewsResponse> => {
  const response = await axios.get(`video/${videoId}/views`, {
    params: {
      ...(since && { since }),
      ...(until && { until }),
    },
  });
  return {
    id: videoId,
    ...response?.data?.content,
  };
};

type UseVideosViewsOptions = {
  videoIds: Array<string>;
  since: string;
  until: string;
};

export const useVideosViews = ({
  videoIds,
  since,
  until,
}: UseVideosViewsOptions): VideoViewsResponse[] => {
  // Generate the queries array
  const queries = videoIds?.map((videoId) => ({
    queryKey: ["videoViews", videoId, since, until],
    queryFn: () => getVideoViews(videoId, since, until),
  }));

  // Use useQueries hook to fetch data for all videoIds in parallel
  const queryResults = useQueries({ queries });

  // todo - add checks to make sure data have the same number of day's count.
  // Extract the data from the query results
  return queryResults
    .filter((r) => r.isSuccess)
    .map((queryResult) => queryResult.data) as VideoViewsResponse[];
};
