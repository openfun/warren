import { createContext } from "react";

type DateContext = {
  since: Date;
  until: Date;
};
// default value to minus 7 day at midnight to today's 23:59:59
const today = new Date();
today.setHours(23, 59, 59);

const oneWeekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000 + 1000); // +1000 to be midnight instead of 23:59:59
export const DateContext = createContext({ since: oneWeekAgo, until: today });
