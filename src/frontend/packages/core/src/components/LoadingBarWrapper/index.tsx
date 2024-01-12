import LoadingBar, { LoadingBarRef } from "react-top-loading-bar";
import React, { useEffect, useRef, useState } from "react";
import { useIsFetching } from "@tanstack/react-query";
import { WARREN_COLOR } from "../../utils";

/**
 * LoadingBarWrapper Component
 *
 * The LoadingBarWrapper component is a wrapper for a loading bar that tracks the
 * progress of fetching operations in the application. It displays a loading bar
 * with a specified color and height.
 *
 * @component
 * @return {JSX.Element} The rendered LoadingBarWrapper component.
 */
export const LoadingBarWrapper: React.FC = () => {
  const ref = useRef<LoadingBarRef>(null);

  const currentFetchCount = useIsFetching();
  const [isStarted, setIsStarted] = useState(false);

  // Explanation: When new data is being fetched, 'currentFetchCount' represents the total number of queries in progress.
  // As each query is completed, 'currentFetchCount' decreases until it reaches 0 when all queries have loaded.
  useEffect(() => {
    if (currentFetchCount > 0 && !isStarted) {
      setIsStarted(true);
      ref.current?.continuousStart();
    } else if (currentFetchCount === 0 && isStarted) {
      setIsStarted(false);
      ref.current?.complete();
    }
  }, [currentFetchCount]);

  return (
    <LoadingBar
      ref={ref}
      containerClassName="c__loading-bar__container"
      color={WARREN_COLOR}
      height={3}
    />
  );
};
