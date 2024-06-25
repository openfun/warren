import React from "react";

export interface CourseData {
  organization: string;
  course_name: string;
  course_run?: string;
}

export interface AppData {
  lti_select_form_jwt: string;
  lti_select_form_action_url: string;
  lti_route: string;
  access: string;
  refresh: string;
  is_instructor: boolean;
  context_title?: string;
  course_info?: CourseData;
  course_id?: string;
}

export interface RoleViews {
  instructor: React.LazyExoticComponent<() => JSX.Element>;
  student: React.LazyExoticComponent<() => JSX.Element>;
}

export interface Routes {
  [key: string]: RoleViews;
}
