import { useContext } from "react";
import { VideoFiltersContext, VideoFiltersContextType } from "../contexts";

export const useVideoFilters = (): VideoFiltersContextType => {
  const value = useContext(VideoFiltersContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store FiltersContextType`);
  }
  return value;
};
