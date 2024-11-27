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

export interface Routes {
  [key: string]: React.LazyExoticComponent<() => JSX.Element>;
}

interface DecodedJwtUserLTI {
  id: string;
  email: string;
}

export interface DecodedJwtLTI {
  consumer_site: string;
  course_id: string;
  exp: number;
  iat: number;
  jti: string;
  locale: string;
  resource_link_description?: string;
  resource_link_id: string;
  roles: Array<string>;
  session_id: string;
  token_type: string;
  user: DecodedJwtUserLTI;
}

export interface ResourceMetricsResponseItem {
  date: string;
  count: number;
}

export interface ResourceMetricsResponse {
  id: string;
  total: number;
  counts: Array<ResourceMetricsResponseItem>;
}

export interface ResourceMetricsQueryParams {
  since: string;
  until: string;
  unique?: boolean;
}

export interface Resource {
  id: string;
  title: string;
}

export interface UseResourceMetricsReturn {
  resourceMetrics: ResourceMetricsResponse[];
  isFetching: boolean;
}
