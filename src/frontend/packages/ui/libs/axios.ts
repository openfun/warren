import Axios from "axios";

const API_BASE_URL = `${
  import.meta.env.VITE_PUBLIC_WARREN_API_ROOT_URL
}/api/v1/`;

export const apiAxios = Axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

const APP_BASE_URL = `${
  import.meta.env.VITE_PUBLIC_WARREN_APP_ROOT_URL
}/api/v1/`;

export const appAxios = Axios.create({
  baseURL: APP_BASE_URL,
});
