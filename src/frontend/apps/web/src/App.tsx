import React from "react";
import AppProvider from "ui/provider/app";
import Filters from "ui/components/filters";
import { DailyViews } from "ui";
import Layout from "../components/Layout";
import { parseDataContext } from "./utils";

const dataContext = parseDataContext();

export const App = () => {
  // todo : store this data in a proper context and initialize the app
  console.log(dataContext); // eslint-disable-line no-console
  return (
    <Layout>
      <AppProvider>
        <Filters />
        <DailyViews />
      </AppProvider>
    </Layout>
  );
};
