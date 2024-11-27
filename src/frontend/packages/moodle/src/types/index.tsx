export enum Activities {
  ASSIGNMENT = "mod_assign",
  LIVE_SESSION = "mod_bigbluebuttonbn",
  BOOK = "mod_book",
  CHAT = "mod_chat",
  CHOICE = "mod_choice",
  DATA = "mod_data",
  MEETING = "mod_facetoface",
  FEEDBACK = "mod_feedback",
  FOLDER = "mod_folder",
  FORUM = "mod_forum",
  GLOSSARY = "mod_glossary",
  IMCSP = "mod_imcsp",
  LESSON = "mod_lesson",
  LTI = "mod_lti",
  PAGE = "mod_page",
  QUIZ = "mod_quiz",
  RESOURCE = "mod_resource",
  SCORM = "mod_scorm",
  SURVEY = "mod_survey",
  URL = "mod_url",
  WIKI = "mod_wiki",
  WORKSHOP = "mod_workshop",
  PROGRAM = "totara_program",
}

export enum ViewsActivities {
  ASSIGNMENT = Activities.ASSIGNMENT,
  LIVE_SESSION = Activities.LIVE_SESSION,
  BOOK = Activities.BOOK,
  CHAT = Activities.CHAT,
  CHOICE = Activities.CHOICE,
  DATA = Activities.DATA,
  MEETING = Activities.MEETING,
  FEEDBACK = Activities.FEEDBACK,
  FOLDER = Activities.FOLDER,
  FORUM = Activities.FORUM,
  GLOSSARY = Activities.GLOSSARY,
  IMCSP = Activities.IMCSP,
  LESSON = Activities.LESSON,
  LTI = Activities.LTI,
  PAGE = Activities.PAGE,
  QUIZ = Activities.QUIZ,
  RESOURCE = Activities.RESOURCE,
  SCORM = Activities.SCORM,
  SURVEY = Activities.SURVEY,
  URL = Activities.URL,
  WIKI = Activities.WIKI,
  WORKSHOP = Activities.WORKSHOP,
}


export interface MoodleResource {
  id: string;
  title: string;
  technical_datatypes: Array<string>;
}