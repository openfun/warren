import React, { useMemo } from "react";
import { SimpleDataGrid } from "@openfun/cunningham-react";
import { Card, useFilters } from "@openfun/warren-core";
import { useVideoFilters } from "../../hooks";
import { useVideosViews } from "../../api";
import { Video, VideoViewsResponse } from "../../types";

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
  } = useFilters();
  const { videos } = useVideoFilters();

  const { videoViews: viewsData } = useVideosViews(videos, { since, until });
  const { videoViews: viewersData } = useVideosViews(videos, {
    since,
    until,
    unique: true,
  });

  const extractTotal = (data: VideoViewsResponse[], id: string) =>
    data?.find((i) => i.id === id)?.total || "-";

  const rows = useMemo(
    () =>
      videos.map((video: Video) => {
        return {
          id: video.id,
          title: video.title,
          views: extractTotal(viewsData, video.id),
          viewer: extractTotal(viewersData, video.id),
        };
      }),
    [videos, viewsData, viewersData],
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
