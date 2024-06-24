import { jwtDecode } from "jwt-decode";

export interface DecodedJwtUserLTI {
  id: string;
  email: string;
}

export interface DecodedJwtLTI {
  consumer_site: string;
  course_id: string;
  exp: number;
  iat: number;
  jti: string;
  locale: string;
  resource_link_description: string;
  resource_link_id: string;
  roles: Array<string>;
  session_id: string;
  token_type: string;
  user: DecodedJwtUserLTI;
}

export const isDecodedJwtLTI = (jwt: unknown): jwt is DecodedJwtLTI => {
  if (jwt && typeof jwt === "object") {
    const courseId = (jwt as DecodedJwtLTI).course_id;
    const userId = (jwt as DecodedJwtLTI).user?.id;
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
