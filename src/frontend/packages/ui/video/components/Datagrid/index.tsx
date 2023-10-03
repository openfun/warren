import React, { useMemo } from "react";
import { DataGrid } from "@openfun/cunningham-react";
import useFilters from "../../hooks/useFilters";
import { Card } from "../../../components/Card";
import { useVideosViews } from "../../api/getVideoViews";
import { VideoViewsResponse } from "../../types";

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
    videoIds,
  } = useFilters();

  const { videoViews: viewsData, isFetching: isViewsFetching } = useVideosViews(
    videoIds,
    { since, until },
  );
  const { videoViews: viewersData, isFetching: isViewersFetching } =
    useVideosViews(videoIds, { since, until, unique: true });

  const extractTotal = (data: VideoViewsResponse[], id: string) =>
    data?.find((i) => i.id === id)?.total || "-";

  const rows = useMemo(
    () =>
      videoIds.map((videoId) => {
        return {
          id: videoId,
          uuid: videoId,
          views: extractTotal(viewsData, videoId),
          viewer: extractTotal(viewersData, videoId),
        };
      }),
    [videoIds, viewsData, viewersData],
  );

  return (
    <Card title="Video data">
      <DataGrid
        columns={[
          {
            field: "uuid",
            headerName: "UUID",
          },
          {
            field: "views",
            headerName: "Total Views",
          },
          {
            field: "viewer",
            headerName: "Total Viewer",
          },
        ]}
        rows={rows}
        isLoading={isViewsFetching || isViewersFetching}
      />
    </Card>
  );
};
