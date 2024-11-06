import { useQueries } from "@tanstack/react-query";
import { AxiosInstance } from "axios";
import {
  useTokenInterceptor,
  apiAxios,
  UseResourceMetricsReturn,
  ResourceMetricsQueryParams,
  ResourceMetricsResponse,
  Resource,
} from "@openfun/warren-core";

export const DEFAULT_BASE_QUERY_KEY = "documentDownloads";

/**
 * Retrieves document downloads data for a specific document with optional filters.
 *
 * @param {AxiosInstance} client - Axios instance for making the API request.
 * @param {string} documentId - The ID of the document to fetch downloads for.
 * @param {ResourceMetricsQueryParams} queryParams - Optional filters for the request.
 * @returns {Promise<ResourceMetricsResponse>} A promise that resolves to the document downloads data.
 */
const getDocumentDownloads = async (
  client: AxiosInstance,
  documentId: string,
  queryParams: ResourceMetricsQueryParams,
): Promise<ResourceMetricsResponse> => {
  const response = await client.get(`document/${documentId}/downloads`, {
    params: Object.fromEntries(
      Object.entries(queryParams).filter(([, value]) => !!value),
    ),
  });
  return {
    id: documentId,
    ...response?.data,
  };
};

/**
 * A custom hook for fetching document downloads data for multiple documents in parallel.
 *
 * @param {Array<Resource>} documents - An array of documents to fetch downloads for.
 * @param {ResourceMetricsQueryParams} queryParams - Optional filters for the requests.
 * @param {boolean} wait - Optional flag to control the order of execution.
 * @param {string} baseQueryKey - Optional base query key.
 * @returns {UseResourceMetricsReturn} An object containing the fetched data and loading status.
 */
export const useDocumentDownloads = (
  documents: Array<Resource>,
  queryParams: ResourceMetricsQueryParams,
  wait: boolean = false,
  baseQueryKey: string = DEFAULT_BASE_QUERY_KEY,
): UseResourceMetricsReturn => {
  const { since, until, unique } = queryParams;

  // Get the API client, set with the authorization headers and refresh mechanism
  const client = useTokenInterceptor(apiAxios);

  // Generate a query object for each document
  const queries = wait
    ? []
    : documents?.map((document) => ({
        queryKey: [baseQueryKey, document.id, since, until, unique || false],
        queryFn: () => getDocumentDownloads(client, document.id, queryParams),
        staleTime: Infinity,
      }));

  // Use useQueries hook to fetch data for all documentIds in parallel
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
