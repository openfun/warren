import dayjs from "dayjs";
import { useQuery } from "@tanstack/react-query";
import { AxiosInstance } from "axios";
import {
  apiAxios,
  ResourceMetricsQueryParams,
  ResourceMetricsResponse,
  UseResourceMetricsReturn,
  useTokenInterceptor,
} from "@openfun/warren-core";

const DEFAULT_BASE_QUERY_KEY = "courseResourceViews";

type CourseResourceViewsQueryParams = ResourceMetricsQueryParams & {
  /**
   * @type {Array<string>}
   * Optional filter for specific module names (e.g., activities or resources) as an array of strings.
   */
  selectedModnames?: Array<string>;
};

/**
 * Fetches course resource views metrics from the server based on provided parameters.
 *
 * @param {AxiosInstance} client - The Axios instance with authorization headers.
 * @param {CourseResourceViewsQueryParams} queryParams - Query parameters including time range
 * and optional module filters.
 * @returns {Promise<Array<ResourceMetricsResponse>>} A promise resolving to an array of
 * resource metrics responses.
 */
const getCourseResourceViews = async (
  client: AxiosInstance,
  queryParams: CourseResourceViewsQueryParams,
): Promise<Array<ResourceMetricsResponse>> => {
  const response = await client.get(`moodle/views`, {
    params: Object.fromEntries(
      Object.entries(queryParams).filter(([, value]) => !!value),
    ),
  });
  return response?.data;
};

/**
 * A custom hook for retrieving course resource views data based on query parameters.
 *
 * @param {CourseResourceViewsQueryParams} queryParams - Parameters for filtering course views data,
 * including time range and optional module names.
 * @param {boolean} [enabled=true] - Optional flag to enable or disable the query; defaults to true.
 * @returns {UseResourceMetricsReturn} An object containing an array of resource metrics and a loading status.
 */
export const useCourseResourceViews = (
  queryParams: CourseResourceViewsQueryParams,
  enabled?: boolean,
): UseResourceMetricsReturn => {
  // Get the API client, set with the authorization headers and refresh mechanism
  const client = useTokenInterceptor(apiAxios);

  const queryResult = useQuery({
    queryKey: [DEFAULT_BASE_QUERY_KEY, queryParams],
    queryFn: () => getCourseResourceViews(client, queryParams),
    staleTime: Infinity,
    enabled,
  });

  const { isFetching, data } = queryResult;

  return {
    resourceMetrics: data || [],
    isFetching,
  };
};
