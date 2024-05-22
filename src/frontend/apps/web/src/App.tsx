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
const videoRoutes: Routes = {
  instructor: lazy(() => import("@openfun/warren-video/src/pages/Instructor")),
  student: lazy(() => import("@openfun/warren-video/src/pages/Student")),
};

const getVideoRoute = (): React.LazyExoticComponent<() => JSX.Element> => {
  if (dataContext.is_instructor) {
    return videoRoutes.instructor;
  } else {
    return videoRoutes.student;
  }
};

const routes: Routes = {
  video: getVideoRoute(),
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
