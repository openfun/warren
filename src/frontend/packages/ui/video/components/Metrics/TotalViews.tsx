import React from "react";
import { ViewsMetric } from "./ViewsMetric";

/**
 * A React functional component that displays the total count of views for selected videos.
 *
 * This component fetches data for views of the selected videos that occurred within the specified date range.
 * It calculates the total count of these views and presents it as a metric.
 *
 * @returns {JSX.Element} The JSX for the TotalViews component.
 */
export const TotalViews: React.FC = () => <ViewsMetric title="Views" />;
