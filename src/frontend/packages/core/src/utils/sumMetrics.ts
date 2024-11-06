import { ResourceMetricsResponse } from "../types";

/**
 * Calculate the total sum of downloads from an array of ResourceMetricsResponse objects.
 * @param {ResourceMetricsResponse[]} metrics - An array of ResourceMetricsResponse objects.
 * @returns {number} The total sum of downloads.
 */
export const sumMetrics = (metrics: ResourceMetricsResponse[]): number =>
  metrics?.length
    ? metrics
        .map((v) => v.total)
        .reduce((previous: number, current: number) => previous + current)
    : 0;
