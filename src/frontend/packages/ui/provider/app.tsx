import React from "react";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "../libs/react-query";
import { CunninghamProvider } from "@openfun/cunningham-react";
import { FiltersProvider } from "../contexts/filtersContext";

type AppProviderProps = {
  children: React.ReactNode;
};

const AppProvider = ({ children }: AppProviderProps) => (
  <CunninghamProvider>
    <FiltersProvider>
      <QueryClientProvider client={queryClient}>
        {children}
        <ReactQueryDevtools initialIsOpen />
      </QueryClientProvider>
    </FiltersProvider>
  </CunninghamProvider>
);
export default AppProvider;