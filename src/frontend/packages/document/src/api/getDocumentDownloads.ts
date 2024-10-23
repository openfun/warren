import { useQueries } from "@tanstack/react-query";
import { AxiosInstance } from "axios";
import { useTokenInterceptor, apiAxios } from "@openfun/warren-core";
import {
  DocumentDownloadsQueryParams,
  DocumentDownloadsResponse,
  Document,
} from "../types";

export const DEFAULT_BASE_QUERY_KEY = "documentDownloads";

/**
 * Retrieves document downloads data for a specific document with optional filters.
 *
 * @param {AxiosInstance} client - Axios instance for making the API request.
 * @param {string} documentId - The ID of the document to fetch downloads for.
 * @param {DocumentDownloadsQueryParams} queryParams - Optional filters for the request.
 * @returns {Promise<DocumentDownloadsResponse>} A promise that resolves to the document downloads data.
 */
const getDocumentDownloads = async (
  client: AxiosInstance,
  documentId: string,
  queryParams: DocumentDownloadsQueryParams,
): Promise<DocumentDownloadsResponse> => {
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

export type UseDocumentDownloadsReturn = {
  documentDownloads: DocumentDownloadsResponse[];
  isFetching: boolean;
};

/**
 * A custom hook for fetching document downloads data for multiple documents in parallel.
 *
 * @param {Array<Document>} documents - An array of documents to fetch downloads for.
 * @param {DocumentDownloadsQueryParams} queryParams - Optional filters for the requests.
 * @param {boolean} wait - Optional flag to control the order of execution.
 * @param {string} baseQueryKey - Optional base query key.
 * @returns {UseDocumentDownloadsReturn} An object containing the fetched data and loading status.
 */
export const useDocumentDownloads = (
  documents: Array<Document>,
  queryParams: DocumentDownloadsQueryParams,
  wait: boolean = false,
  baseQueryKey: string = DEFAULT_BASE_QUERY_KEY,
): UseDocumentDownloadsReturn => {
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
  const documentDownloads = queryResults
    .filter((r) => r.isSuccess)
    .map((queryResult) => queryResult.data) as DocumentDownloadsResponse[];

  return {
    documentDownloads,
    isFetching,
  };
};
