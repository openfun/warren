import React, { LazyExoticComponent, lazy } from "react";
import {
  AppContentLoader,
  parseDataContext,
  Routes,
  AppLayout,
  AppProvider,
} from "@openfun/warren-core";

const dataContext = parseDataContext(document);


const pathName: string = "video";
const packageName: string = "@openfun/warren-video";

// todo - brainstorm on an autodiscovery mechanism for routes
const routes: Routes = {};

routes[pathName] = {
  instructor: lazy(() => import(`../../../node_modules/${packageName}/src/pages/Instructor`)),
  student: lazy(() => import(`../../../node_modules/${packageName}/src/pages/Student/index.tsx`)),
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
