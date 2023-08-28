import React from "react";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClientProvider } from "@tanstack/react-query";
import { CunninghamProvider } from "@openfun/cunningham-react";
import { queryClient } from "../libs/react-query";
import { FiltersProvider } from "../contexts/filtersContext";
import { LTIProvider } from "../contexts/LTIContext";

type AppProviderProps = {
  children: React.ReactNode;
};

const AppProvider = ({ children }: AppProviderProps) => (
  <CunninghamProvider>
    <LTIProvider>
      <FiltersProvider>
        <QueryClientProvider client={queryClient}>
          {children}
          <ReactQueryDevtools initialIsOpen />
        </QueryClientProvider>
      </FiltersProvider>
    </LTIProvider>
  </CunninghamProvider>
);
export default AppProvider;
