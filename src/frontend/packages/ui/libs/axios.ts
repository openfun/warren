import Axios from "axios";

export const axios = Axios.create({
  baseURL: `${process.env.NEXT_PUBLIC_WARREN_BACKEND_ROOT_URL}/api/v1/`,
});
