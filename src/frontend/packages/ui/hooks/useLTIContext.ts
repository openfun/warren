import { useContext } from "react";
import LTIContext, { LTIContextType } from "../contexts/LTIContext";

const useLTIContext = (): LTIContextType => {
  const value = useContext(LTIContext);
  if (!value) {
    throw new Error(`Missing wrapping Provider for Store LTIContextType`);
  }
  return value;
};

export default useLTIContext;
