import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { getDefaultDates } from "../utils";

export interface FiltersContextType {
  date: [string, string];
  videoIds: Array<string>;
  setDate: Dispatch<SetStateAction<[string, string]>>;
  setVideoIds: Dispatch<SetStateAction<Array<string>>>;
}

const FiltersContext = createContext<FiltersContextType | null>(null);

export const FiltersProvider: React.FC<{ children: any }> = ({ children }) => {
  const defaultDates = getDefaultDates();
  // todo - Rethink naming + format the dates are stored
  const [date, setDate] = useState<[string, string]>(defaultDates);
  const [videoIds, setVideoIds] = useState<Array<string>>([]);

  const value = useMemo(
    () => ({ date, setDate, videoIds, setVideoIds }),
    [date, videoIds],
  );

  return (
    <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>
  );
};

export default FiltersContext;
