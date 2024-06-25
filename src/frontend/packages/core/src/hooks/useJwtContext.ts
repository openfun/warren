import { useContext } from "react";
import { JwtContext, JwtContextType } from "../contexts";

export const useJwtContext = (): JwtContextType => {
  const value = useContext(JwtContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store JwtContextType`);
  }
  return value;
};
