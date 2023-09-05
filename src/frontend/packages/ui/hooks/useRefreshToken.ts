import { AxiosInstance } from "axios";
import { AppData } from "../types";
import useLTIContext from "./useLTIContext";

const useRefreshToken = (client: AxiosInstance) => {
  const { appData, setAppData } = useLTIContext();

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

    return newAccessToken;
  };

  return refreshAccessToken;
};

export default useRefreshToken;
