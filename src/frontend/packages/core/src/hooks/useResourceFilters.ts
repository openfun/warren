import { useContext } from "react";
import {
  ResourceFiltersContext,
  ResourceFiltersContextType,
} from "../contexts";

export const useResourceFilters = (): ResourceFiltersContextType => {
  const value = useContext(ResourceFiltersContext);
  if (!value) {
    throw new Error(
      `Missing wrapping Provider for Store ResourceFiltersContextType`,
    );
  }
  return value;
};
