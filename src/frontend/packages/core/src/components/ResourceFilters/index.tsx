import React from "react";
import { Select } from "@openfun/cunningham-react";
import { DateFilters } from "../DateFilters";
import { useResourceFilters } from "../../hooks";
import { Resource } from "../../types";

export type ResourceOption = {
  value: string;
  label: string;
};

// FIXME - refactor this part with the prototype of Experience Index.
export const RESOURCES: Array<Resource> = [
  { id: "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50", title: "Resource 1" },
  { id: "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d", title: "Resource 2" },
  { id: "uuid://541dab6b-50ae-4444-b230-494f0621f132", title: "Resource 3" },
  { id: "uuid://69d32ad5-3af5-4160-a995-87e09da6865c", title: "Resource 4" },
  { id: "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb", title: "Resource 5" },
  { id: "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e", title: "Resource 6" },
  { id: "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0", title: "Resource 7" },
  { id: "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7", title: "Resource 8" },
  { id: "uuid://dd38149d-956a-483d-8975-c1506de1e1a9", title: "Resource 9" },
  { id: "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b", title: "Resource 10" },
];

export type ResourceFiltersProps = {
  label: string;
};
/**
 * A React functional component for filtering documents and specifying a date range.
 *
 * This component provides user interface elements to select documents from a list,
 * specify a date range, and trigger a data refresh.
 * @param {label} string - The label name for the resources.
 *
 */
export const ResourceFilters: React.FC<ResourceFiltersProps> = ({ label }) => {
  const { setResources } = useResourceFilters();

  const getResourceOptions = (): ResourceOption[] => {
    return RESOURCES.map((item) => ({
      value: item.id,
      label: item.title,
    }));
  };

  const handleResourceIdsChange = (
    value: string | string[] | number | undefined,
  ): void => {
    if (typeof value === "number") {
      return;
    }

    setResources(RESOURCES.filter((resource) => value?.includes(resource.id)));
  };

  return (
    <DateFilters>
      <Select
        label={label}
        defaultValue={RESOURCES[0].id}
        options={getResourceOptions()}
        multi={true}
        monoline={true}
        onChange={(selectedValues) =>
          handleResourceIdsChange(selectedValues.target.value)
        }
      />
    </DateFilters>
  );
};
