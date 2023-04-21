import React, { useState, useEffect } from "react";

import { DateRangePicker as RSuiteDateRangePicker } from 'rsuite';
import { DateRange } from "rsuite/esm/DateRangePicker";
import '../styles/main.css';

type DateRangePickerProps = {
  title: String
  onDateChange: (since: number, until: number) => void
}

// TODO: add format, start and end date in props
export const DateRangePicker = ({title = "Filter by date", onDateChange}: DateRangePickerProps) => {

  const onDateValueChange = (value: DateRange | null, event: React.SyntheticEvent<Element, Event>) => {
    if (value) {
      onDateChange(value[0].getTime(), value[1].getTime())
    }
  }
return (
     <>
        <p>{title}</p>
        <RSuiteDateRangePicker
          format="yyyy-MM-dd HH:mm:ss"
          defaultCalendarValue={[new Date('2023-03-01 00:00:00'), new Date('2022-05-01 23:59:59')]}
          onChange={onDateValueChange}
          
      />;
      </>
  );
}
