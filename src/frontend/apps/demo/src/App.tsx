import React from "react";
import AppProvider from "ui/provider/app";
import Layout from "../components/Layout";
import { AppInitializer } from "./AppInitializer";

export const App = () => {
  return (
    <Layout>
      <AppProvider>
        <AppInitializer />
      </AppProvider>
    </Layout>
  );
};
