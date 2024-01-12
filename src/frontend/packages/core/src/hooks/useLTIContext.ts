import { useContext } from "react";
import { LtiContext, LTIContextType } from "../contexts";

export const useLTIContext = (): LTIContextType => {
  const value = useContext(LtiContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store LTIContextType`);
  }
  return value;
};
