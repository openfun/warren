import React from "react";
import { ViewsMetric } from "./ViewsMetric";

/**
 * A React functional component that displays the total count of complete viewers for selected videos.
 *
 * This component fetches data for unique viewers who have watched the selected videos at least once within the specified date range.
 * A complete viewer is defined as an individual who has watched a video at least once and has a total watch time exceeding
 * the video's completion threshold. It then calculates and displays the total count of such complete viewers as a metric.
 *
 * @returns {JSX.Element} The JSX for the CompleteViewers component.
 */
export const CompleteViewers: React.FC = () => (
  <ViewsMetric
    title="Complete viewers"
    tooltip="Viewer who has watched a video at least once and has a total watch time exceeding the video's completion threshold."
    complete
    unique
  />
);
