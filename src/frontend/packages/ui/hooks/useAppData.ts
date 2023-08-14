import { useContext } from "react";
import AppDataContext, { AppDataContextType } from "../contexts/appDataContext";

const useAppData = (): AppDataContextType => {
  const value = useContext(AppDataContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store AppDataContextType`);
  }
  return value;
};

export default useAppData;
