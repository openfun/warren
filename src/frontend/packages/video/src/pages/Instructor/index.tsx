import {
  Flexgrid,
  ResourceFilters,
  ResourceFiltersProvider,
} from "@openfun/warren-core";
import { DailyViews, VideosData } from "../../components";
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
      <ResourceFiltersProvider>
        <ResourceFilters label="Videos" />
        <Flexgrid>
          <DailyViews />
          <VideosData />
        </Flexgrid>
      </ResourceFiltersProvider>
    </div>
  );
};
