import { useContext } from "react";
import {
  DocumentFiltersContext,
  DocumentFiltersContextType,
} from "../contexts";

export const useDocumentFilters = (): DocumentFiltersContextType => {
  const value = useContext(DocumentFiltersContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store FiltersContextType`);
  }
  return value;
};
