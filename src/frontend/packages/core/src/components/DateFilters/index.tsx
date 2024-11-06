import React, { ReactNode } from "react";
import { DateRangePicker } from "@openfun/cunningham-react";
import dayjs from "dayjs";
import { useDateFilters } from "../../hooks";
import { formatDates, getDefaultDates } from "../../utils";

export type DateFiltersProps = {
  children: ReactNode;
};

/**
 * A React functional component for specifying a date range.
 *
 * @component
 * @returns {JSX.Element} - The rendered Filters component with date range picker.
 */
export const DateFilters: React.FC<DateFiltersProps> = ({
  children,
}: DateFiltersProps) => {
  const { date, setDate } = useDateFilters();

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
