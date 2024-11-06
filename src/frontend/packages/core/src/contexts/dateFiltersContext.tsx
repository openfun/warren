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
  setDate: Dispatch<SetStateAction<[string, string]>>;
}

export const FiltersContext = createContext<FiltersContextType | null>(null);

export const FiltersProvider: React.FC<{ children: any }> = ({ children }) => {
  const defaultDates = getDefaultDates();
  const [date, setDate] = useState<[string, string]>(defaultDates);

  const value = useMemo(() => ({ date, setDate }), [date]);

  return (
    <FiltersContext.Provider value={value}>{children}</FiltersContext.Provider>
  );
};
