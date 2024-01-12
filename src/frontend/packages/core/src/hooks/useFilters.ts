import { useContext } from "react";
import { FiltersContext, FiltersContextType } from "../contexts";

export const useFilters = (): FiltersContextType => {
  const value = useContext(FiltersContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store FiltersContextType`);
  }
  return value;
};
