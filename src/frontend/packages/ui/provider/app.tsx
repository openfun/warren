import React from "react";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClientProvider } from "@tanstack/react-query";
import { CunninghamProvider } from "@openfun/cunningham-react";
import { queryClient } from "../libs/react-query";
import { FiltersProvider } from "../contexts/filtersContext";
import { AppDataProvider } from "../contexts/appDataContext";

type AppProviderProps = {
  children: React.ReactNode;
};

const AppProvider = ({ children }: AppProviderProps) => (
  <CunninghamProvider>
    <AppDataProvider>
      <FiltersProvider>
        <QueryClientProvider client={queryClient}>
          {children}
          <ReactQueryDevtools initialIsOpen />
        </QueryClientProvider>
      </FiltersProvider>
    </AppDataProvider>
  </CunninghamProvider>
);
export default AppProvider;
