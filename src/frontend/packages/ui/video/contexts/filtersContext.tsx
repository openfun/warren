import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { getDefaultDates } from "../utils";
import { Video } from "../components/Filters";

export interface FiltersContextType {
  date: [string, string];
  videos: Array<Video>;
  setDate: Dispatch<SetStateAction<[string, string]>>;
  setVideos: Dispatch<SetStateAction<Array<Video>>>;
}

const FiltersContext = createContext<FiltersContextType | null>(null);

export const FiltersProvider: React.FC<{ children: any }> = ({ children }) => {
  const defaultDates = getDefaultDates();
  // todo - Rethink naming + format the dates are stored
  const [date, setDate] = useState<[string, string]>(defaultDates);
  const [videos, setVideos] = useState<Array<string>>([]);

  const value = useMemo(
    () => ({ date, setDate, videos, setVideos }),
    [date, videos],
  );

  return (
    <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>
  );
};

export default FiltersContext;
