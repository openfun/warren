import React, { lazy, useMemo, Suspense } from "react";
import useLTIContext from "ui/hooks/useLTIContext";
import { AppData } from "ui/types";

interface ContentComponents {
  [key: string]: React.LazyExoticComponent<() => JSX.Element>;
}

const Contents: ContentComponents = {
  select: lazy(() => import("../SelectContent")),
  demo: lazy(() => import("ui/video/pages/Overview/index")),
};

interface AppContentLoaderProps {
  dataContext: AppData;
}

export const AppContentLoader = ({ dataContext }: AppContentLoaderProps) => {
  const { setAppData } = useLTIContext();
  setAppData(dataContext);

  const Content = useMemo(() => {
    // todo - render a fallback if the lti route is invalid
    return Contents[dataContext.lti_route];
  }, [dataContext]);

  return (
    <Suspense fallback={<div>loading</div>}>
      <Content />
    </Suspense>
  );
};
