import { DocumentDownloadsResponse } from "../types";

/**
 * Calculate the total sum of downloads from an array of DocumentDownloadsResponse objects.
 * @param {DocumentDownloadsResponse[]} downloads - An array of DocumentDownloadsResponse objects.
 * @returns {number} The total sum of downloads.
 */
export const sumDownloads = (downloads: DocumentDownloadsResponse[]): number =>
  downloads?.length
    ? downloads
        .map((v) => v.total)
        .reduce((previous: number, current: number) => previous + current)
    : 0;
