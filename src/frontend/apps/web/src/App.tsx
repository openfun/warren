import React, { lazy } from "react";
import {
  AppContentLoader,
  parseDataContext,
  Routes,
  AppLayout,
  AppProvider,
} from "@openfun/warren-core";

const dataContext = parseDataContext(document);

// todo - brainstorm on an autodiscovery mechanism for routes
const routes: Routes = {
  demo: lazy(() => import("@openfun/warren-video/src/pages/Overview")),
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
