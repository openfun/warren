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

export const LtiContext = createContext<LTIContextType | null>(null);

export const LTIProvider: React.FC<{ children: any }> = ({ children }) => {
  const [appData, setAppData] = useState<any>({});

  const value = useMemo(() => ({ appData, setAppData }), [appData]);
  return <LtiContext.Provider value={value}>{children}</LtiContext.Provider>;
};
