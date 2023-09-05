import { useEffect } from "react";
import { AxiosInstance } from "axios";
import { appAxios } from "../libs/axios";
import useLTIContext from "./useLTIContext";
import useRefreshToken from "./useRefreshToken";

const useTokenInterceptor = (client: AxiosInstance) => {
  const {
    appData: { access, refresh },
  } = useLTIContext();

  const refreshAccessToken = useRefreshToken(appAxios);

  useEffect(() => {
    const requestIntercept = client.interceptors.request.use(
      (config) => {
        if (!config.headers.Authorization) {
          config.headers.Authorization = `Bearer ${access}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    const responseIntercept = client.interceptors.response.use(
      (response) => response,
      async (error) => {
        // todo - simplify
        const prevRequest = error?.config;

        if (error?.response?.status === 401 && !prevRequest?.sent) {
          const newAccessToken = await refreshAccessToken();

          const modifiedRequest = {
            ...prevRequest,
            headers: { Authorization: `Bearer ${newAccessToken}` },
            sent: true,
          };

          return client(modifiedRequest);
        }
        return Promise.reject(error);
      },
    );

    return () => {
      client.interceptors.request.eject(requestIntercept);
      client.interceptors.response.eject(responseIntercept);
    };
  }, [access, refresh]);

  return client;
};

export default useTokenInterceptor;
