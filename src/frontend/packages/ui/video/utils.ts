import dayjs, { Dayjs } from "dayjs";
import utc from "dayjs/plugin/utc";
import { VideoViewsResponse } from "./types";

dayjs.extend(utc);

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

/**
 * Format a pair of date values to the start or end of the day.
 *
 * This function takes an array of two date values and formats each date to either the start or end of the day based on its position in the array.
 *
 * @param {Array} dates - An array of two date values, where the first date represents the start date and the second date represents the end date.
 * @returns {Array} An array of two formatted ISO date strings representing the start and end of the day for the provided dates.
 */
export const formatDates = (dates: [string | Dayjs, string | Dayjs]) => {
  const formatDay = (d: string | Dayjs, isStart: boolean) =>
    dayjs(d)[isStart ? "startOf" : "endOf"]("day");

  const [startDate, endDate] = dates.map((d, index) =>
    formatDay(d, index === 0),
  );

  // FIXME - Handle daylight saving time (DST) and standard time (STD) disparities within the API.
  return [startDate.utcOffset(endDate.utcOffset(), true), endDate].map((v) =>
    v.format(),
  );
};

/**
 * Get default start and end dates for a date range.
 * The default range duration is 'DEFAULT_RANGE_DURATION' days.
 *
 * @returns {[string, string]} An array containing the default start and end dates.
 */
export const getDefaultDates = (): [string, string] => {
  const DEFAULT_RANGE_DURATION = 7;
  const endDate = dayjs();
  const startDate = endDate.subtract(DEFAULT_RANGE_DURATION, "day");
  return formatDates([startDate, endDate]);
};
