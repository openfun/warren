export type DocumentDownloadsResponseItem = {
  date: string;
  count: number;
};

export type DocumentDownloadsResponse = {
  id: string;
  total: number;
  counts: Array<DocumentDownloadsResponseItem>;
};

export type DocumentDownloadsQueryParams = {
  since: string;
  until: string;
  unique?: boolean;
};

export type Document = {
  id: string;
  title: string;
};
