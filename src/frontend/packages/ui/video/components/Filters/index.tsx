import React from "react";
import { DateRangePicker, Select, Button } from "@openfun/cunningham-react";
import useFilters from "../../hooks/useFilters";
import { queryClient } from "../../../libs/react-query";

type VideoOption = {
  value: string;
  label: string;
};

// FIXME - refactor this part with the prototype of Experience Index.
const VIDEO_IDS = [
  "uuid://0aecfa93-cef3-45ae-b7f5-a603e9e45f50",
  "uuid://1c0c127a-f121-4bd1-8db6-918605c2645d",
  "uuid://541dab6b-50ae-4444-b230-494f0621f132",
  "uuid://69d32ad5-3af5-4160-a995-87e09da6865c",
  "uuid://7d4f3c70-1e79-4243-9b7d-166076ce8bfb",
  "uuid://8d386f48-3baa-4acf-8a46-0f2be4ae243e",
  "uuid://b172ec09-97ec-4651-bc57-6eabebf47ed0",
  "uuid://d613b564-5d18-4238-a69c-0fc8cee5d0e7",
  "uuid://dd38149d-956a-483d-8975-c1506de1e1a9",
  "uuid://e151ee65-7a72-478c-ac57-8a02f19e748b",
];

/**
 * A React functional component for filtering videos and specifying a date range.
 *
 * This component provides user interface elements to select videos from a list,
 * specify a date range, and trigger a data refresh.
 *
 */
export const Filters: React.FC = () => {
  const { date, setDate, setVideoIds } = useFilters();

  const getVideoOptions = (): VideoOption[] => {
    return VIDEO_IDS.map((item) => ({
      value: item,
      label: item.slice(-5),
    }));
  };

  const handleVideoIdsChange = (
    value: string | number | string[] | undefined,
  ): void => {
    let videoIds: string[] = [];

    if (Array.isArray(value)) {
      videoIds = value;
    } else if (value !== undefined) {
      videoIds = [value.toString()];
    }
    setVideoIds(videoIds);
  };

  const handleDateChange = (value: [string, string] | null): void => {
    // FIXME - handle start at 00:00:00 and end at 23:59:59
    if (value) {
      setDate(value);
    } else {
      setDate(["", ""]);
    }
  };

  return (
    <div className="c__filters">
      <Select
        label="Videos"
        defaultValue={VIDEO_IDS[0]}
        options={getVideoOptions()}
        multi={true}
        onChange={(e) => handleVideoIdsChange(e.target.value)}
      />
      <DateRangePicker
        className="c__filters__range-picker"
        startLabel="Start"
        endLabel="End"
        value={date}
        onChange={(value) => handleDateChange(value)}
      />
      <Button
        className="c__filters__refresh"
        aria-label="Refresh dashboard"
        color="tertiary"
        icon={<span className="material-icons">cached</span>}
        onClick={() => queryClient.refetchQueries({ type: "active" })}
      />
    </div>
  );
};
