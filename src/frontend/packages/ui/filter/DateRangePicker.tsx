import React, { useContext, useState, useEffect } from "react";

import { DateRangePicker as RSuiteDateRangePicker } from "rsuite";
import { DateRange } from "rsuite/esm/DateRangePicker";
import "../styles/main.css";

import { DateContext } from "../DateContext";

type DateRangePickerProps = {
  title: String;
  onDateChange: (since: Date, until: Date) => void;
};

// TODO: add format, start and end date in props
export const DateRangePicker = ({
  title = "Filter by date",
  onDateChange,
}: DateRangePickerProps) => {
  const onDateValueChange = (
    value: DateRange | null,
    event: React.SyntheticEvent<Element, Event>
  ) => {
    if (value) {
      onDateChange(value[0], value[1]);
    }
  };

  const { since, until } = useContext(DateContext);

  return (
    <>
      <p>{title}</p>
      <RSuiteDateRangePicker
        format="yyyy-MM-dd HH:mm:ss"
        defaultCalendarValue={[since, until]}
        onChange={onDateValueChange}
      />
      ;
    </>
  );
};
