import React, { useMemo } from "react";
import { SimpleDataGrid } from "@openfun/cunningham-react";
import {
  Card,
  useDateFilters,
  ResourceMetricsResponse,
} from "@openfun/warren-core";
import { useCourseResourceViews } from "../../api";
import { useModnameFilters, useResourceFilters } from "../../hooks";
import { MoodleResource } from "../../types";
/**
 * A React component for displaying a data grid of selected resources within a specified date range.
 * This component retrieves and presents resource downloads and downloaders data.
 *
 * This initial implementation will be completed with more metadata on the resource as soon as the
 * experience index is available.
 *
 * @returns {JSX.Element} The JSX for the resourcesData component.
 */
export const ResourcesData: React.FC = () => {
  const {
    date: [since, until],
  } = useDateFilters();
  const { resources } = useResourceFilters();
  const { selectedModnames } = useModnameFilters();

  const { resourceMetrics: viewsData } = useCourseResourceViews({
    since,
    until,
    selectedModnames
  });
  const { resourceMetrics: viewersData } = useCourseResourceViews({
    since,
    until,
    selectedModnames,
    unique: true,
  });

  const extractTotal = (data: ResourceMetricsResponse[], id: string) =>
    data?.find((i) => i.id === id)?.total || "-";

  const rows = useMemo(
    () =>
      resources.map((resource: MoodleResource) => {
        return {
          id: resource.id,
          title: resource.title,
          modname: resource.technical_datatypes[0],
          downloads: extractTotal(viewsData, resource.id),
          downloader: extractTotal(viewersData, resource.id),
        };
      }),
    [resources, viewsData, viewersData],
  );

  return (
    <Card title="Resources data">
      <SimpleDataGrid
        columns={[
          {
            field: "title",
            headerName: "Title",
          },
          {
            field: "views",
            headerName: "Views",
          },
          {
            field: "viewer",
            headerName: "Viewers",
          },
        ]}
        rows={rows}
      />
    </Card>
  );
};
