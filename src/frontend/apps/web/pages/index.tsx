import type { ReactElement } from "react";
import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import Layout from "../components/Layout";
import type { NextPageWithLayout } from "./_app";

import { Total, DateRangePicker, DailyViewsAreaGraph } from "ui";
import { DateContext } from "ui/DateContext";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
    },
  },
});



const Web: NextPageWithLayout = () => {
  const videoIds = [
    "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50",
    "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d",
    "uuid://541dab6b-50ae-4444-b230-494f0621f132",
    "uuid://69d32ad5-3af5-4160-a995-87e09da6865c",
    "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb",
    "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e",
    "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0",
    "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7",
    "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
    "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b",
  ];
  const title: String = "filter dates:"

  const [since, setSince] = useState(0)
  const [until, setUntil] = useState(9999999999999)

  const updateSinceAndUntil = (newStartingDateUnixMs: number, newEndDateUnixMs: number) => {
    setSince(newStartingDateUnixMs);
    setUntil(newEndDateUnixMs);
  }

  return (
    <>
      <DateRangePicker title={title} onDateChange={updateSinceAndUntil} />
      <QueryClientProvider client={queryClient}>
        <DateContext.Provider value={{since, until}}>
          <DailyViewsAreaGraph videoIds={videoIds}/>
          <Total videoIds={videoIds} />
          <ReactQueryDevtools initialIsOpen />
        </DateContext.Provider>
      </QueryClientProvider>
    </>

  );
};

Web.getLayout = function getLayout(page: ReactElement) {
  return <Layout>{page}</Layout>;
};

export default Web;
