export type VideoViewsResponseItem = {
  date: string;
  count: number;
};

export type VideoViewsResponse = {
  id: string;
  total: number;
  counts: Array<VideoViewsResponseItem>;
};
