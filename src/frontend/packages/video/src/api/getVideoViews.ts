import { useQueries } from "@tanstack/react-query";
import { AxiosInstance } from "axios";
import {
  useTokenInterceptor,
  apiAxios,
  ResourceMetricsQueryParams,
  ResourceMetricsResponse,
  Resource,
  UseResourceMetricsReturn,
} from "@openfun/warren-core";

export const DEFAULT_BASE_QUERY_KEY = "videoViews";

type VideoViewsQueryParams = ResourceMetricsQueryParams & {
  complete?: boolean;
};

/**
 * Retrieves video views data for a specific video with optional filters.
 *
 * @param {AxiosInstance} client - Axios instance for making the API request.
 * @param {string} videoId - The ID of the video to fetch views for.
 * @param {VideoViewsQueryParams} queryParams - Optional filters for the request.
 * @returns {Promise<ResourceMetricsResponse>} A promise that resolves to the video views data.
 */
const getVideoViews = async (
  client: AxiosInstance,
  videoId: string,
  queryParams: VideoViewsQueryParams,
): Promise<ResourceMetricsResponse> => {
  const response = await client.get(`video/${videoId}/views`, {
    params: Object.fromEntries(
      Object.entries(queryParams).filter(([, value]) => !!value),
    ),
  });
  return {
    id: videoId,
    ...response?.data,
  };
};

/**
 * A custom hook for fetching video views data for multiple videos in parallel.
 *
 * @param {Array<Resource>} videos - An array of videos to fetch views for.
 * @param {VideoViewsQueryParams} queryParams - Optional filters for the requests.
 * @param {boolean} wait - Optional flag to control the order of execution.
 * @param {string} baseQueryKey - Optional base query key.
 * @returns {UseVideoViewsReturn} An object containing the fetched data and loading status.
 */
export const useVideosViews = (
  videos: Array<Resource>,
  queryParams: VideoViewsQueryParams,
  wait: boolean = false,
  baseQueryKey: string = DEFAULT_BASE_QUERY_KEY,
): UseResourceMetricsReturn => {
  const { since, until, unique, complete } = queryParams;

  // Get the API client, set with the authorization headers and refresh mechanism
  const client = useTokenInterceptor(apiAxios);

  // Generate a query object for each video
  const queries = wait
    ? []
    : videos?.map((video) => ({
        queryKey: [
          baseQueryKey,
          video.id,
          since,
          until,
          unique || false,
          complete || false,
        ],
        queryFn: () => getVideoViews(client, video.id, queryParams),
        staleTime: Infinity,
      }));

  // Use useQueries hook to fetch data for all videoIds in parallel
  const queryResults = useQueries({ queries });
  const isFetching = queryResults.some((r) => r.isFetching);

  // Extract the data from the successful query results
  const resourceMetrics = queryResults
    .filter((r) => r.isSuccess)
    .map((queryResult) => queryResult.data) as ResourceMetricsResponse[];

  return {
    resourceMetrics,
    isFetching,
  };
};
