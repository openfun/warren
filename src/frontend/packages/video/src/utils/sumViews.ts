import { VideoViewsResponse } from "../types";

/**
 * Calculate the total sum of views from an array of VideoViewsResponse objects.
 * @param {VideoViewsResponse[]} views - An array of VideoViewsResponse objects.
 * @returns {number} The total sum of views.
 */
export const sumViews = (views: VideoViewsResponse[]): number =>
  views?.length
    ? views
        .map((v) => v.total)
        .reduce((previous: number, current: number) => previous + current)
    : 0;
