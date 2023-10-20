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
  context_title?: string;
  course_info?: CourseData;
}
