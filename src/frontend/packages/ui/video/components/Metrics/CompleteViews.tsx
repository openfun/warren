import React from "react";
import { ViewsMetric } from "./ViewsMetric";

/**
 * A React functional component that displays the total number of complete views for selected videos.
 *
 * This component retrieves data for views of the selected videos that occurred at least once within the specified
 * date range and have a watch time exceeding the video's completion threshold. It then calculates the total count
 * of such complete views and displays it as a metric.
 *
 * @returns {JSX.Element} The JSX for the CompleteViews component.
 */
export const CompleteViews: React.FC = () => (
  <ViewsMetric
    title="Complete views"
    tooltip="View with a watch time that exceeds the video's completion threshold."
    complete
  />
);
