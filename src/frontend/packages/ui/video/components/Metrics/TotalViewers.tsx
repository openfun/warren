import React from "react";
import { ViewsMetric } from "./ViewsMetric";

/**
 * A React functional component that displays the total count of unique viewers who have watched the selected videos.
 *
 * This component retrieves data for unique viewers who have watched the selected videos at least once within the provided date range.
 * It subsequently calculates the overall count of these unique viewers and presents it as a metric.
 *
 * @returns {JSX.Element} The JSX for the TotalViewers component.
 */
export const TotalViewers: React.FC = () => (
  <ViewsMetric title="Viewers" unique />
);
