import { jwtDecode } from "jwt-decode";
import { DecodedJwtLTI } from "../types";

export const isDecodedJwtLTI = (jwt: unknown): jwt is DecodedJwtLTI => {
  if (jwt && typeof jwt === "object") {
    const courseId = (jwt as DecodedJwtLTI).course_id;
    const userId = (jwt as DecodedJwtLTI).user.id;
    const { roles } = jwt as DecodedJwtLTI;

    return !!courseId && !!userId && !!roles;
  }

  return false;
};

export const decodeJwtLTI = (jwtToDecode?: string): DecodedJwtLTI => {
  if (!jwtToDecode) {
    throw new Error(
      "Impossible to decode JWT token, there is no jwt to decode.",
    );
  }

  const jwt = jwtDecode(jwtToDecode);

  if (isDecodedJwtLTI(jwt)) {
    return jwt;
  }

  throw new Error("JWT token is invalid");
};
