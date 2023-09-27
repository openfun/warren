import { DailyViews } from "../../components/Views";
import { Filters } from "../../components/Filters";
import { Autogrid } from "../../../components/Autogrid";
import {
  TotalViews,
  CompleteViews,
  TotalViewers,
  CompleteViewers,
} from "../../components/Metrics";

/**
 * A React component responsible for rendering a dashboard overview of video statistics.
 *
 * This component combines the Filters component for selecting date ranges and videos, with the DailyViews component
 * to display daily video statistics. It serves as a dashboard overview of all videos' statistical data.
 *
 * @returns {JSX.Element} The JSX for the videos statistics overview dashboard.
 */
export default () => {
  return (
    <div className="c__overview">
      <Filters />
      <Autogrid>
        <TotalViews />
        <CompleteViews />
        <TotalViewers />
        <CompleteViewers />
      </Autogrid>
      <DailyViews />
    </div>
  );
};
