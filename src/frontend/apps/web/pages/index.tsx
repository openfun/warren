import type { ReactElement } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import Layout from "../components/Layout";
import type { NextPageWithLayout } from "./_app";

import { DailyViews } from "ui";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});

const Web: NextPageWithLayout = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <h1>Warren.</h1>
      <DailyViews videoId="uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e" />
      <DailyViews videoId="uuid://541dab6b-50ae-4444-b230-494f0621f132" />
      <ReactQueryDevtools initialIsOpen />
    </QueryClientProvider>
  );
};

Web.getLayout = function getLayout(page: ReactElement) {
  return <Layout>{page}</Layout>;
};

export default Web;
