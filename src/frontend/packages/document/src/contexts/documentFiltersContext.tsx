import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { Document } from "../types";

export interface DocumentFiltersContextType {
  documents: Array<Document>;
  setDocuments: Dispatch<SetStateAction<Array<Document>>>;
}

export const DocumentFiltersContext =
  createContext<DocumentFiltersContextType | null>(null);

export const DocumentFiltersProvider: React.FC<{ children: any }> = ({
  children,
}) => {
  const [documents, setDocuments] = useState<Array<Document>>([]);
  const value = useMemo(() => ({ documents, setDocuments }), [documents]);

  return (
    <DocumentFiltersContext.Provider value={value}>
      {children}
    </DocumentFiltersContext.Provider>
  );
};
