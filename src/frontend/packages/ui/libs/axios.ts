import Axios from "axios";

export const axios = Axios.create({
  baseURL: `${import.meta.env.VITE_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/`,
});
