import React, { useContext, useState, useEffect } from "react";

import { DateRangePicker as RSuiteDateRangePicker } from "rsuite";
import { DateRange } from "rsuite/esm/DateRangePicker";
import "../styles/main.css";

import { DateContext } from "../DateContext";

type DateRangePickerProps = {
  title: String;
  onDateChange: (since: Date, until: Date) => void;
};

export const DateRangePicker = ({
  title = "Filter by date",
  onDateChange,
}: DateRangePickerProps) => {

  const { since, until } = useContext(DateContext);

  const [dateRange, setDateRange] = useState<DateRange|null>([since, until])

  useEffect( () => {
    setDateRange([since, until])
  }, [])


  const onDateValueChange = (
    value: DateRange | null,
    event: React.SyntheticEvent<Element, Event>
  ) => {
    if (value) {
      setDateRange(value)
      onDateChange(value[0], value[1]);
    }
  };



  return (
    <>
      <p>{title}</p>
      <RSuiteDateRangePicker
        format="yyyy-MM-dd HH:mm:ss"
        defaultValue={dateRange}
        onChange={onDateValueChange}
      />
      ;
    </>
  );
};
