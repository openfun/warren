import { useContext } from "react";
import { ModnameFiltersContext, ModnameFiltersContextType } from "../contexts";

export const useModnameFilters = (): ModnameFiltersContextType => {
  const value = useContext(ModnameFiltersContext);
  if (!value) {
    throw new Error(
      `Missing wrapping Provider for Store ModnameFiltersContextType`,
    );
  }
  return value;
};
