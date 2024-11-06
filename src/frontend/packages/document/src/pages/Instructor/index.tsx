import {
  Flexgrid,
  ResourceFilters,
  ResourceFiltersProvider,
} from "@openfun/warren-core";
import { DocumentsData, DailyDownloads } from "../../components";
/**
 * A React component responsible for rendering a dashboard overview of document statistics.
 *
 * This component combines the Filters component for selecting date ranges and documents, with the DailyDownloads component
 * to display daily document statistics. It serves as a dashboard overview of all documents' statistical data.
 *
 * @returns {JSX.Element} The JSX for the documents statistics overview dashboard.
 */
export default () => {
  return (
    <div className="c__overview">
      <ResourceFiltersProvider>
        <ResourceFilters label="Documents" />
        <Flexgrid>
          <DailyDownloads />
          <DocumentsData />
        </Flexgrid>
      </ResourceFiltersProvider>
    </div>
  );
};
