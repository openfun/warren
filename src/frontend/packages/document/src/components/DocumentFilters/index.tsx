import React from "react";
import { Select } from "@openfun/cunningham-react";
import { Filters } from "@openfun/warren-core";
import { Document } from "../../types";
import { useDocumentFilters } from "../../hooks";

export type DocumentOption = {
  value: string;
  label: string;
};

// FIXME - refactor this part with the prototype of Experience Index.
export const DOCUMENTS: Array<Document> = [
  { id: "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50", title: "Lesson 1" },
  { id: "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d", title: "Lesson 2" },
  { id: "uuid://541dab6b-50ae-4444-b230-494f0621f132", title: "Lesson 3" },
  { id: "uuid://69d32ad5-3af5-4160-a995-87e09da6865c", title: "Lesson 4" },
  { id: "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb", title: "Lesson 5" },
  { id: "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e", title: "Lesson 6" },
  { id: "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0", title: "Lesson 7" },
  { id: "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7", title: "Lesson 8" },
  { id: "uuid://dd38149d-956a-483d-8975-c1506de1e1a9", title: "Lesson 9" },
  { id: "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b", title: "Lesson 10" },
];

/**
 * A React functional component for filtering documents and specifying a date range.
 *
 * This component provides user interface elements to select documents from a list,
 * specify a date range, and trigger a data refresh.
 *
 */
export const DocumentFilters: React.FC = () => {
  const { setDocuments } = useDocumentFilters();

  const getDocumentOptions = (): DocumentOption[] => {
    return DOCUMENTS.map((item) => ({
      value: item.id,
      label: item.title,
    }));
  };

  const handleDocumentIdsChange = (
    value: string | string[] | number | undefined,
  ): void => {
    if (typeof value === "number") {
      return;
    }

    setDocuments(DOCUMENTS.filter((document) => value?.includes(document.id)));
  };

  return (
    <Filters>
      <Select
        label="Documents"
        defaultValue={DOCUMENTS[0].id}
        options={getDocumentOptions()}
        multi={true}
        monoline={true}
        onChange={(selectedValues) =>
          handleDocumentIdsChange(selectedValues.target.value)
        }
      />
    </Filters>
  );
};
