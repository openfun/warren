import React, { useMemo } from "react";
import { CourseData } from "../../types";

export type BreadCrumbProps = {
  courseInfo?: CourseData;
};

// todo - to be replaced by a proper breadcrumb
export const BreadCrumb: React.FC<BreadCrumbProps> = ({ courseInfo }) => {
  const content = useMemo(
    () => courseInfo && Object.values(courseInfo).reverse().join(" > "),
    [courseInfo],
  );
  return <div>{content}</div>;
};
