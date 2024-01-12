import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import { formatDates } from "./formatDates";

dayjs.extend(utc);

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
