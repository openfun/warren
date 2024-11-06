import React, { useMemo } from "react";
import { SimpleDataGrid } from "@openfun/cunningham-react";
import {
  Card,
  useDateFilters,
  useResourceFilters,
  ResourceMetricsResponse,
  Resource,
} from "@openfun/warren-core";
import { useVideosViews } from "../../api";

/**
 * A React component for displaying a data grid of selected videos within a specified date range.
 * This component retrieves and presents video views and viewers data.
 *
 * This initial implementation will be completed with more metadata on the video as soon as the
 * experience index is available.
 *
 * @returns {JSX.Element} The JSX for the VideosData component.
 */
export const VideosData: React.FC = () => {
  const {
    date: [since, until],
  } = useDateFilters();
  const { resources } = useResourceFilters();

  const { resourceMetrics: viewsData } = useVideosViews(resources, {
    since,
    until,
  });
  const { resourceMetrics: viewersData } = useVideosViews(resources, {
    since,
    until,
    unique: true,
  });

  const extractTotal = (data: ResourceMetricsResponse[], id: string) =>
    data?.find((i) => i.id === id)?.total || "-";

  const rows = useMemo(
    () =>
      resources.map((video: Resource) => {
        return {
          id: video.id,
          title: video.title,
          views: extractTotal(viewsData, video.id),
          viewer: extractTotal(viewersData, video.id),
        };
      }),
    [resources, viewsData, viewersData],
  );

  return (
    <Card title="Video data">
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
