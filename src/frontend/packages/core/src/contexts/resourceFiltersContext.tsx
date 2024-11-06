import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { Resource } from "../types";

export interface ResourceFiltersContextType {
  resources: Array<Resource>;
  setResources: Dispatch<SetStateAction<Array<Resource>>>;
}

export const ResourceFiltersContext =
  createContext<ResourceFiltersContextType | null>(null);

export const ResourceFiltersProvider: React.FC<{ children: any }> = ({
  children,
}) => {
  const [resources, setResources] = useState<Array<Resource>>([]);
  const value = useMemo(() => ({ resources, setResources }), [resources]);

  return (
    <ResourceFiltersContext.Provider value={value}>
      {children}
    </ResourceFiltersContext.Provider>
  );
};
