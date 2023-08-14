import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";

export interface AppDataContextType {
  data: any;
  setData: Dispatch<SetStateAction<any>>;
}

const AppDataContext = createContext<AppDataContextType | null>(null);

export const AppDataProvider: React.FC<{ children: any }> = ({ children }) => {
  const [data, setData] = useState<any>({});

  const context = useMemo(() => ({ data, setData }), [data]);
  return (
    <AppDataContext.Provider value={context}>
      {children}
    </AppDataContext.Provider>
  );
};

export default AppDataContext;
