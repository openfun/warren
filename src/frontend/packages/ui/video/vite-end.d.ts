/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_PUBLIC_WARREN_BACKEND_ROOT_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
