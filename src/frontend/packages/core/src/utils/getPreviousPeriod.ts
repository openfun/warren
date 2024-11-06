import dayjs from "dayjs";
import { formatDates } from "./formatDates";

/**
 * Calculate the previous time period based on the provided since and until dates.
 *
 * This function calculates the start and end dates of the previous time period relative to the given 'since' and 'until' dates.
 * It computes the duration of the selected period and calculates the previous period's start and end dates accordingly.
 *
 * @param {string} since - The start date of the current period.
 * @param {string} until - The end date of the current period.
 * @returns {string[]} An array of two ISO date strings representing the start and end dates of the previous time period.
 */
export const getPreviousPeriod = (since: string, until: string) => {
  const periodDuration = dayjs(until).diff(since, "day") + 1;
  return formatDates([
    dayjs(since).subtract(periodDuration, "day"),
    dayjs(since).subtract(1, "day"),
  ]);
};
