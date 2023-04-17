import React, { useState, useEffect } from "react";

import { DateRangePicker as RSuiteDateRangePicker } from 'rsuite';
import '../styles/main.css';

// type DateRangePickerProps = {
//   title: String
// }

// TODO: add format, start and end date in props
export const DateRangePicker = () => {
   return (
     <>
        {/* <p>{title}</p> */}
        <RSuiteDateRangePicker
          format="yyyy-MM-dd HH:mm:ss"
          defaultCalendarValue={[new Date('2023-03-01 00:00:00'), new Date('2022-05-01 23:59:59')]}
      />;
      </>
  );
}
