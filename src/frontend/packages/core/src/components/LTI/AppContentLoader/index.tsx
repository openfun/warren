import React, { useMemo, Suspense, useEffect } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { SelectContent } from "../SelectContent";
import { useLTIContext } from "../../../hooks";
import { AppData, Routes } from "../../../types";
import { BoundaryScreenError } from "../../BoundaryScreenError";

export interface AppContentLoaderProps {
  dataContext: AppData;
  routes: Routes;
}

function fallbackRender({ error }: { error: Error }) {
  return <BoundaryScreenError message={error.message} />;
}

/**
 * AppContentLoader component dynamically renders content based on the provided data context and route configuration.
 * Data context contains an LTI route, which indicates the right views to render.
 *
 * @component
 * @param {object} props - The properties of the AppContentLoader component.
 * @param {AppData} props.dataContext - An object representing the data context for the application.
 * @param {Routes} props.routes - An object representing the route configuration for the application.
 * @returns {JSX.Element} - The JSX element representing the dynamically loaded content.
 */
export const AppContentLoader: React.FC<AppContentLoaderProps> = ({
  dataContext,
  routes,
}: AppContentLoaderProps) => {
  const { setAppData } = useLTIContext();

  useEffect(() => {
    setAppData(dataContext);
  }, []);

  const routesName = useMemo(() => Object.keys(routes), [routes]);

  // todo - brainstorm on how to avoid this hardcoded string
  if (dataContext.lti_route === "select") {
    return <SelectContent routes={routesName} />;
  }

  if (!routesName.includes(dataContext.lti_route)) {
    return <div>Wrong route</div>;
  }

  // const getRoleRoute = (route: RoleViews): React.LazyExoticComponent<() => JSX.Element> => {
  //   return dataContext.is_instructor ? route.instructor : route.student;
  // };

  const Content = useMemo(
    () => dataContext.is_instructor ?
      routes[dataContext.lti_route].instructor :
      routes[dataContext.lti_route].student,
    [dataContext, routes],
  );

  return (
    <ErrorBoundary fallbackRender={fallbackRender}>
      <Suspense fallback={<div>loading</div>}>
        <Content />
      </Suspense>
    </ErrorBoundary>
  );
};
