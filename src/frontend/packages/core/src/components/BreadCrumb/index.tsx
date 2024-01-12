import React, { useMemo } from "react";
import { CourseData } from "../../types";

export type BreadCrumbProps = {
  courseInfo?: CourseData;
};

/**
 * BreadCrumb component displays breadcrumb navigation based on the provided course information.
 *
 * Filters out empty course info before reversing and joining them with the separator " > ".
 * This component needs to be replaced by a proper BreadCrumb navigation from Cunningham.
 *
 * @component
 * @param {object} props - The properties of the BreadCrumb component.
 * @param {CourseData} props.courseInfo - An object containing course information used to generate breadcrumb navigation.
 * @returns {JSX.Element} - The rendered BreadCrumb component with breadcrumb navigation based on course information.
 */
export const BreadCrumb: React.FC<BreadCrumbProps> = ({ courseInfo }) => {
  const content = useMemo(
    () =>
      courseInfo &&
      Object.values(courseInfo).filter(Boolean).reverse().join(" > "),
    [courseInfo],
  );
  return <div>{content}</div>;
};
