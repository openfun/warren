import React from "react";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClientProvider } from "@tanstack/react-query";
import { CunninghamProvider } from "@openfun/cunningham-react";
import { queryClient } from "../libs";
import { FiltersProvider, LTIProvider } from "../contexts";

export type AppProviderProps = {
  children: React.ReactNode;
};

/**
 * AppProvider component serves as a higher-order component (HOC) that wraps the application with multiple context providers.
 *
 * @component
 * @example
 * // Usage in your application
 * <AppProvider>
 *   {/* Your application components here *}
 * </AppProvider>
 *
 * @param {object} props - The properties of the AppProvider component.
 * @param {React.ReactNode} props.children - The child components that will be wrapped by the context providers.
 * @returns {JSX.Element} - The JSX element representing the wrapped application with context providers.
 */
export const AppProvider = ({ children }: AppProviderProps) => (
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
