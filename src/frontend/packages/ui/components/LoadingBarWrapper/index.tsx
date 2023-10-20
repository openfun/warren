import LoadingBar from "react-top-loading-bar";
import React, { useEffect, useState } from "react";
import { useIsFetching } from "@tanstack/react-query";
import { WARREN_COLOR } from "../../utils";

// Visually indicate to the user that loading has started, even before the first query completes.
// Initialize the loading progress to a value greater than 0.
const INITIAL_PROGRESS = 2;

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
  const currentFetchCount = useIsFetching();
  const [initialFetchCount, setInitialFetchCount] = useState(0);
  const [loadingProgress, setLoadingProgress] = useState(0);

  // Explanation: When new data is being fetched, 'currentFetchCount' represents the total number of queries in progress.
  // As each query is completed, 'currentFetchCount' decreases until it reaches 0 when all queries have loaded.
  useEffect(() => {
    if (initialFetchCount === 0 && currentFetchCount) {
      setInitialFetchCount(currentFetchCount);
      setLoadingProgress(INITIAL_PROGRESS);
    } else if (initialFetchCount !== 0) {
      setLoadingProgress(
        (100 / initialFetchCount) * (initialFetchCount - currentFetchCount),
      );
    }
  }, [currentFetchCount]);

  const handleLoaderFinished = () => {
    setLoadingProgress(0);
    setInitialFetchCount(0);
  };

  return (
    <LoadingBar
      containerClassName="c__loading-bar__container"
      color={WARREN_COLOR}
      height={3}
      progress={loadingProgress}
      onLoaderFinished={handleLoaderFinished}
    />
  );
};
