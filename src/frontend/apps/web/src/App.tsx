import React, { lazy } from "react";
import {
  AppContentLoader,
  AppLayout,
  AppProvider,
  parseDataContext,
  Routes,
} from "@openfun/warren-core";

const dataContext = parseDataContext(document);

// todo - brainstorm on an autodiscovery mechanism for routes
const routes: Routes = {
  demo: lazy(() => import("./Overview.ts")),
};


export const App = () => {
  return (
    <AppProvider>
      <AppLayout>
        <AppContentLoader dataContext={dataContext} routes={routes} />
      </AppLayout>
    </AppProvider>
  );
};
