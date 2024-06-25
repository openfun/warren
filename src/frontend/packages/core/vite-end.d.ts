/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_PUBLIC_WARREN_API_ROOT_URL: string;
  readonly VITE_PUBLIC_WARREN_APP_ROOT_URL: string;
  // readonly VITE_PUBLIC_WARREN_PLUGINS: { [path: string]: string };
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
