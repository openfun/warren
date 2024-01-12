export type VideoViewsResponseItem = {
  date: string;
  count: number;
};

export type VideoViewsResponse = {
  id: string;
  total: number;
  counts: Array<VideoViewsResponseItem>;
};

export type VideoViewsQueryParams = {
  since: string;
  until: string;
  unique?: boolean;
  complete?: boolean;
};

export type Video = {
  id: string;
  title: string;
};
