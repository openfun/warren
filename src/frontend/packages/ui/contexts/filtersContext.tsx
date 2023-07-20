import React, {
  createContext,
  Dispatch,
  SetStateAction,
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
  return (
    <FiltersContext.Provider value={{ date, setDate, videoIds, setVideoIds }}>
      {children}
    </FiltersContext.Provider>
  );
};

export default FiltersContext;
