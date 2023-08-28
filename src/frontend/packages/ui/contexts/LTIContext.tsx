import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { AppData } from "../types";

export interface LTIContextType {
  appData: AppData;
  setAppData: Dispatch<SetStateAction<any>>;
}

const LTIContext = createContext<LTIContextType | null>(null);

export const LTIProvider: React.FC<{ children: any }> = ({ children }) => {
  const [appData, setAppData] = useState<any>({});

  const value = useMemo(() => ({ appData, setAppData }), [appData]);
  return <LTIContext.Provider value={value}>{children}</LTIContext.Provider>;
};

export default LTIContext;
