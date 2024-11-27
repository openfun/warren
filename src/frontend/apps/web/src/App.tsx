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

const documentRoutes: Routes = {
  instructor: lazy(
    () => import("@openfun/warren-document/src/pages/Instructor"),
  ),
  student: lazy(() => import("@openfun/warren-document/src/pages/Student")),
};

const getDocumentRoute = (): React.LazyExoticComponent<() => JSX.Element> => {
  if (dataContext.is_instructor) {
    return documentRoutes.instructor;
  } else {
    return documentRoutes.student;
  }
};

const moodleRoutes: Routes = {
  instructor: lazy(() => import("@openfun/warren-moodle/src/pages/Instructor")),
  student: lazy(() => import("@openfun/warren-moodle/src/pages/Student")),
};

const getMoodleRoute = (): React.LazyExoticComponent<() => JSX.Element> => {
  if (dataContext.is_instructor) {
    return moodleRoutes.instructor;
  } else {
    return moodleRoutes.student;
  }
};

const routes: Routes = {
  video: getVideoRoute(),
  document: getDocumentRoute(),
  moodle: getMoodleRoute(),
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
