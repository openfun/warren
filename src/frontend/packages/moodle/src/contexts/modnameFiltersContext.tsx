import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";

export interface ModnameFiltersContextType {
  selectedModnames: Array<string>;  // Rename to match component usage
  setModnames: Dispatch<SetStateAction<Array<string>>>;
}

export const ModnameFiltersContext =
  createContext<ModnameFiltersContextType | null>(null);

export const ModnameFiltersProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [selectedModnames, setModnames] = useState<Array<string>>([]);  // Use consistent naming
  const value = useMemo(() => ({ selectedModnames, setModnames }), [selectedModnames]);

  return (
    <ModnameFiltersContext.Provider value={value}>
      {children}
    </ModnameFiltersContext.Provider>
  );
};

