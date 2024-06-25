import { AxiosInstance } from "axios";
import { AppData } from "../types";
import { decodeJwtLTI } from "../utils";
import { useLTIContext } from "./useLTIContext";
import { useJwtContext } from "./useJwtContext";

export const useRefreshToken = (client: AxiosInstance) => {
  const { appData, setAppData } = useLTIContext();
  const { setDecodedJwt } = useJwtContext();

  const refreshAccessToken = async () => {
    const response = await client.post("token/refresh/", {
      refresh: appData.refresh,
    });

    const newAccessToken = response.data.access;

    // Update appData with the new access token
    setAppData((prevData: AppData) => ({
      ...prevData,
      access: newAccessToken,
    }));
    // Decode the new access token as the JWT token
    setDecodedJwt(decodeJwtLTI(newAccessToken));

    return newAccessToken;
  };

  return refreshAccessToken;
};
