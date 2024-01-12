import dayjs, { Dayjs } from "dayjs";
import utc from "dayjs/plugin/utc";

dayjs.extend(utc);

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
