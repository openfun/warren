import React, {
    createContext,
    Dispatch,
    SetStateAction,
    useMemo,
    useState,
  } from "react";
  import { MoodleResource } from "../types";
  
  export interface ResourceFiltersContextType {
    resources: Array<MoodleResource>;
    setResources: Dispatch<SetStateAction<Array<MoodleResource>>>;
  }
  
  export const ResourceFiltersContext =
    createContext<ResourceFiltersContextType | null>(null);
  
  export const ResourceFiltersProvider: React.FC<{ children: any }> = ({
    children,
  }) => {
    const [resources, setResources] = useState<Array<MoodleResource>>([]);
    const value = useMemo(() => ({ resources, setResources }), [resources]);
  
    return (
      <ResourceFiltersContext.Provider value={value}>
        {children}
      </ResourceFiltersContext.Provider>
    );
  };
  