import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";

export interface FiltersContextType {
  date: [string, string];
  videoIds: Array<string>;
  setDate: Dispatch<SetStateAction<[string, string]>>;
  setVideoIds: Dispatch<SetStateAction<Array<string>>>;
}

const FiltersContext = createContext<FiltersContextType | null>(null);

export const FiltersProvider: React.FC<{ children: any }> = ({ children }) => {
  const [date, setDate] = useState<[string, string]>(["", ""]);
  const [videoIds, setVideoIds] = useState<Array<string>>([]);

  const context = useMemo(
    () => ({ date, setDate, videoIds, setVideoIds }),
    [date, videoIds],
  );
  return (
    <FiltersContext.Provider value={context}>
      {children}
    </FiltersContext.Provider>
  );
};

export default FiltersContext;
