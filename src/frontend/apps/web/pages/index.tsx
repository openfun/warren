import type { ReactElement } from "react";
import Layout from "../components/Layout";
import type { NextPageWithLayout } from "./_app";

import { DailyViews } from "ui";
import AppProvider from "ui/provider/app";
import Filters from "ui/components/filters";

const Web: NextPageWithLayout = () => {
  return (
    <AppProvider>
      <Filters />
      <DailyViews />
    </AppProvider>
  );
};

Web.getLayout = function getLayout(page: ReactElement) {
  return <Layout>{page}</Layout>;
};

export default Web;
