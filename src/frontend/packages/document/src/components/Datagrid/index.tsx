import React, { useMemo } from "react";
import { SimpleDataGrid } from "@openfun/cunningham-react";
import { Card, useFilters } from "@openfun/warren-core";
import { useDocumentFilters } from "../../hooks";
import { useDocumentDownloads } from "../../api";
import { Document, DocumentDownloadsResponse } from "../../types";

/**
 * A React component for displaying a data grid of selected documents within a specified date range.
 * This component retrieves and presents document downloads and downloaders data.
 *
 * This initial implementation will be completed with more metadata on the document as soon as the
 * experience index is available.
 *
 * @returns {JSX.Element} The JSX for the DocumentsData component.
 */
export const DocumentsData: React.FC = () => {
  const {
    date: [since, until],
  } = useFilters();
  const { documents } = useDocumentFilters();

  const { documentDownloads: downloadsData } = useDocumentDownloads(documents, {
    since,
    until,
  });
  const { documentDownloads: downloadersData } = useDocumentDownloads(
    documents,
    {
      since,
      until,
      unique: true,
    },
  );

  const extractTotal = (data: DocumentDownloadsResponse[], id: string) =>
    data?.find((i) => i.id === id)?.total || "-";

  const rows = useMemo(
    () =>
      documents.map((document: Document) => {
        return {
          id: document.id,
          title: document.title,
          downloads: extractTotal(downloadsData, document.id),
          downloader: extractTotal(downloadersData, document.id),
        };
      }),
    [documents, downloadsData, downloadersData],
  );

  return (
    <Card title="Document data">
      <SimpleDataGrid
        columns={[
          {
            field: "title",
            headerName: "Title",
          },
          {
            field: "downloads",
            headerName: "Downloads",
          },
          {
            field: "downloader",
            headerName: "Downloaders",
          },
        ]}
        rows={rows}
      />
    </Card>
  );
};
