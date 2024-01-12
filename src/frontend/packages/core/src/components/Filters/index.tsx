import React, { ReactNode } from "react";
import { DateRangePicker } from "@openfun/cunningham-react";
import dayjs from "dayjs";
import { useFilters } from "../../hooks";
import { formatDates, getDefaultDates } from "../../utils";

export type FiltersProps = {
  children: ReactNode;
};

/**
 * A React functional component for specifying a date range.
 *
 * @component
 * @returns {JSX.Element} - The rendered Filters component with date range picker.
 */
export const Filters: React.FC<FiltersProps> = ({ children }: FiltersProps) => {
  const { date, setDate } = useFilters();

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
      {children}
      <DateRangePicker
        className="c__filters__range-picker"
        startLabel="Start"
        endLabel="End"
        maxValue={dayjs().endOf("day").format()}
        value={date}
        onChange={(value) => handleDateChange(value)}
      />
    </div>
  );
};
