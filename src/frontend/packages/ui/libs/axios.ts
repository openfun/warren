import Axios from "axios";

// Retrieve Warren API root URL from Django Template global variable or Vite environment.
const API_BASE_URL = `${
  API_ROOT_URL || import.meta.env.VITE_PUBLIC_WARREN_API_ROOT_URL
}/api/v1/`;

export const apiAxios = Axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Retrieve Warren App's API root URL from Django Template global variable or Vite environment.
const APP_BASE_URL = `${
  APP_ROOT_URL || import.meta.env.VITE_PUBLIC_WARREN_APP_ROOT_URL
}/api/v1/`;

export const appAxios = Axios.create({
  baseURL: APP_BASE_URL,
});
