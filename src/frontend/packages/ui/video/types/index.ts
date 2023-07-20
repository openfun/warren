export type VideoViewsResponseItem = {
  date: string;
  count: number;
};

export type VideoViewsResponse = {
  id: string;
  total_views: number;
  count_by_date: Array<VideoViewsResponseItem>;
};
