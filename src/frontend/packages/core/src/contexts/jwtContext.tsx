import React, {
  createContext,
  Dispatch,
  SetStateAction,
  useMemo,
  useState,
} from "react";
import { DecodedJwtLTI } from "../types";

export interface JwtContextType {
  decodedJwt: DecodedJwtLTI;
  setDecodedJwt: Dispatch<SetStateAction<any>>;
}

export const JwtContext = createContext<JwtContextType | null>(null);

export const JwtProvider: React.FC<{ children: any }> = ({ children }) => {
  const [decodedJwt, setDecodedJwt] = useState<any>({});

  const value = useMemo(() => ({ decodedJwt, setDecodedJwt }), [decodedJwt]);

  return <JwtContext.Provider value={value}>{children}</JwtContext.Provider>;
};
