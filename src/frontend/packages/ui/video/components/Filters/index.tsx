import React from "react";
import { DateRangePicker, Select, Button } from "@openfun/cunningham-react";
import dayjs from "dayjs";
import useFilters from "../../hooks/useFilters";
import { queryClient } from "../../../libs/react-query";
import { formatDates, getDefaultDates } from "../../utils";

export type Video = {
  id: string;
  title: string;
};

type VideoOption = {
  value: string;
  label: string;
};

// FIXME - refactor this part with the prototype of Experience Index.
export const VIDEOS: Array<Video> = [
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
 * A React functional component for filtering videos and specifying a date range.
 *
 * This component provides user interface elements to select videos from a list,
 * specify a date range, and trigger a data refresh.
 *
 */
export const Filters: React.FC = () => {
  const { date, setDate, setVideos } = useFilters();

  const getVideoOptions = (): VideoOption[] => {
    return VIDEOS.map((item) => ({
      value: item.id,
      label: item.title,
    }));
  };

  const handleVideoIdsChange = (value: string[] | undefined): void => {
    setVideos(VIDEOS.filter((video) => value?.includes(video.id)));
  };

  const handleDateChange = (value: [string, string] | null): void => {
    if (value) {
      setDate(formatDates(value));
    } else {
      const defaultDates = getDefaultDates();
      setDate(defaultDates);
    }
  };

  return (
    <div className="c__filters">
      <Select
        label="Videos"
        defaultValue={VIDEOS[0].id}
        options={getVideoOptions()}
        multi={true}
        onChange={(e) => handleVideoIdsChange(e.target.value)}
      />
      <DateRangePicker
        className="c__filters__range-picker"
        startLabel="Start"
        endLabel="End"
        maxValue={dayjs().endOf("day").format()}
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
