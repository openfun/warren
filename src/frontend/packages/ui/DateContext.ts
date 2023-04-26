import { createContext } from "react";

type DateContext = {
  since: Date;
  until: Date;
};
const now = new Date();
const oneWeekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
export const DateContext = createContext({ since: oneWeekAgo, until: now });
