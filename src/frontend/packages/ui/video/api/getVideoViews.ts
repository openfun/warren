import { useQueries } from "@tanstack/react-query";
import { AxiosInstance } from "axios";
import { VideoViewsResponse } from "../types";
import { apiAxios } from "../../libs/axios";
import useTokenInterceptor from "../../hooks/useTokenInterceptor";

const getVideoViews = async (
  client: AxiosInstance,
  videoId: string,
  since: string,
  until: string,
): Promise<VideoViewsResponse> => {
  const response = await client.get(`video/${videoId}/views`, {
    params: {
      ...(since && { since }),
      ...(until && { until }),
    },
  });
  return {
    id: videoId,
    ...response?.data,
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
  // Get the API client, set with the authorization headers and refresh mechanism
  const client = useTokenInterceptor(apiAxios);

  // Generate the queries array
  const queries = videoIds?.map((videoId) => ({
    queryKey: ["videoViews", videoId, since, until],
    queryFn: () => getVideoViews(client, videoId, since, until),
  }));

  // Use useQueries hook to fetch data for all videoIds in parallel
  const queryResults = useQueries({ queries });

  // todo - add checks to make sure data have the same number of day's count.
  // Extract the data from the query results
  return queryResults
    .filter((r) => r.isSuccess)
    .map((queryResult) => queryResult.data) as VideoViewsResponse[];
};
