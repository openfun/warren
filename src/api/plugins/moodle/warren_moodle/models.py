"""Defines the schema of what is returned inside the API responses."""

from enum import Enum


class Activities(Enum):
    """Moodle activities' types."""

    ASSIGNMENT = "mod_assign"
    LIVE_SESSION = "mod_bigbluebuttonbn"
    BOOK = "mod_book"
    CHAT = "mod_chat"
    CHOICE = "mod_choice"
    DATA = "mod_data"
    MEETING = "mod_facetoface"
    FEEDBACK = "mod_feedback"
    FOLDER = "mod_folder"
    FORUM = "mod_forum"
    GLOSSARY = "mod_glossary"
    IMCSP = "mod_imcsp"
    LESSON = "mod_lesson"
    LTI = "mod_lti"
    PAGE = "mod_page"
    QUIZ = "mod_quiz"
    RESOURCE = "mod_resource"
    SCORM = "mod_scorm"
    SURVEY = "mod_survey"
    URL = "mod_url"
    WIKI = "mod_wiki"
    WORKSHOP = "mod_workshop"
    PROGRAM = "totara_program"


class Events(Enum):
    """Moodle Logstore xAPI events types."""

    COURSE_COMPLETED = "\\core\\event\\course_completed"
    COURSE_VIEWED = "\\core\\event\\course_viewed"
    USER_CREATED = "\\core\\event\\user_created"
    USER_ENROLMENT_CREATED = "\\core\\event\\user_enrolment_created"
    USER_LOGGEDIN = "\\core\\event\\user_loggedin"
    USER_LOGGEDOUT = "\\core\\event\\user_loggedout"
    COURSE_MODULE_COMPLETION_UPDATED = "\\core\\event\\course_module_completion_updated"
    ASSESSABLE_SUBMITTED = "\\mod_assign\\event\\assessable_submitted"
    SUBMISSION_GRADED = "\\mod_assign\\event\\submission_graded"
    ACTIVITY_VIEWED = "\\mod_bigbluebuttonbn\\event\\activity_viewed"
    ACTIVITY_MANAGEMENT_VIEWED = (
        "\\mod_bigbluebuttonbn\\event\\activity_management_viewed"
    )
    LIVE_SESSION_EVENT = "\\mod_bigbluebuttonbn\\event\\live_session_event"
    MEETING_CREATED = "\\mod_bigbluebuttonbn\\event\\meeting_created"
    MEETING_ENDED = "\\mod_bigbluebuttonbn\\event\\meeting_ended"
    MEETING_JOINED = "\\mod_bigbluebuttonbn\\event\\meeting_joined"
    MEETING_LEFT = "\\mod_bigbluebuttonbn\\event\\meeting_left"
    RECORDING_DELETED = "\\mod_bigbluebuttonbn\\event\\recording_deleted"
    RECORDING_EDITED = "\\mod_bigbluebuttonbn\\event\\recording_edited"
    RECORDING_IMPORTED = "\\mod_bigbluebuttonbn\\event\\recording_imported"
    RECORDING_PROTECTED = "\\mod_bigbluebuttonbn\\event\\recording_protected"
    RECORDING_PUBLISHED = "\\mod_bigbluebuttonbn\\event\\recording_published"
    RECORDING_UNPROTECTED = "\\mod_bigbluebuttonbn\\event\\recording_unprotected"
    RECORDING_UNPUBLISHED = "\\mod_bigbluebuttonbn\\event\\recording_unpublished"
    RECORDING_VIEWED = "\\mod_bigbluebuttonbn\\event\\recording_viewed"
    BOOK_MODULE_VIEWED = "\\mod_book\\event\\course_module_viewed"
    CHAPTER_VIEWED = "\\mod_book\\event\\chapter_viewed"
    CHAT_MODULE_VIEWED = "\\mod_chat\\event\\course_module_viewed"
    MESSAGE_SENT = "\\mod_chat\\event\\message_sent"
    CHOICE_MODULE_VIEWED = "\\mod_choice\\event\\course_module_viewed"
    ANSWER_CREATED = "\\mod_choice\\event\\answer_created"
    DATA_MODULE_VIEWED = "\\mod_data\\event\\course_module_viewed"
    RECORD_CREATED = "\\mod_data\\event\\record_created"
    RECORD_UPDATED = "\\mod_data\\event\\record_updated"
    CANCEL_BOOKING = "\\mod_facetoface\\event\\cancel_booking"
    FACETOFACE_MODULE_VIEWED = "\\mod_facetoface\\event\\course_module_viewed"
    SIGNUP_SUCCESS = "\\mod_facetoface\\event\\signup_success"
    TAKE_ATTENDANCE = "\\mod_facetoface\\event\\take_attendance"
    FEEDBACK_MODULE_VIEWED = "\\mod_feedback\\event\\course_module_viewed"
    RESPONSE_SUBMITTED = "\\mod_feedback\\event\\response_submitted"
    FOLDER_MODULE_VIEWED = "\\mod_folder\\event\\course_module_viewed"
    FORUM_MODULE_VIEWED = "\\mod_forum\\event\\course_module_viewed"
    DISCUSSION_CREATED = "\\mod_forum\\event\\discussion_created"
    DISCUSSION_VIEWED = "\\mod_forum\\event\\discussion_viewed"
    POST_CREATED = "\\mod_forum\\event\\post_created"
    USER_REPORT_VIEWED = "\\mod_forum\\event\\user_report_viewed"
    GLOSSARY_MODULE_VIEWED = "\\mod_glossary\\event\\course_module_viewed"
    ENTRY_CREATED = "\\mod_glossary\\event\\entry_created"
    ENTRY_UPDATED = "\\mod_glossary\\event\\entry_updated"
    IMSCP_MODULE_VIEWED = "\\mod_imscp\\event\\course_module_viewed"
    LESSON_MODULE_VIEWED = "\\mod_lesson\\event\\course_module_viewed"
    LESSON_ENDED = "\\mod_lesson\\event\\lesson_ended"
    LTI_MODULE_VIEWED = "\\mod_lti\\event\\course_module_viewed"
    PAGE_MODULE_VIEWED = "\\mod_page\\event\\course_module_viewed"
    QUIZ_MODULE_VIEWED = "\\mod_quiz\\event\\course_module_viewed"
    ATTEMPT_ABANDONED = "\\mod_quiz\\event\\attempt_abandoned"
    ATTEMPT_STARTED = "\\mod_quiz\\event\\attempt_started"
    ATTEMPT_REVIEWED = "\\mod_quiz\\event\\attempt_reviewed"
    ATTEMPT_SUBMITTED = "\\mod_quiz\\event\\attempt_submitted"
    ATTEMPT_VIEWED = "\\mod_quiz\\event\\attempt_viewed"
    RESOURCE_MODULE_VIEWED = "\\mod_resource\\event\\course_module_viewed"
    SCORM_MODULE_VIEWED = "\\mod_scorm\\event\\course_module_viewed"
    SCO_LAUNCHED = "\\mod_scorm\\event\\sco_launched"
    SCORERAW_SUBMITTED = "\\mod_scorm\\event\\scoreraw_submitted"
    STATUS_SUBMITTED = "\\mod_scorm\\event\\status_submitted"
    SURVEY_MODULE_VIEWED = "\\mod_survey\\event\\course_module_viewed"
    SURVEY_RESPONSE_SUBMITTED = "\\mod_survey\\event\\response_submitted"
    URL_MODULE_VIEWED = "\\mod_url\\event\\course_module_viewed"
    WIKI_MODULE_VIEWED = "\\mod_wiki\\event\\course_module_viewed"
    PAGE_UPDATED = "\\mod_wiki\\event\\page_updated"
    PAGE_VIEWED = "\\mod_wiki\\event\\page_viewed"
    WORKSHOP_MODULE_VIEWED = "\\mod_workshop\\event\\course_module_viewed"
    SUBMISSION_CREATED = "\\mod_workshop\\event\\submission_created"
    SUBMISSION_ASSESSED = "\\mod_workshop\\event\\submission_assessed"
    PROGRAM_ASSIGNED = "\\totara_program\\event\\program_assigned"


class ViewsEvents(Enum):
    """Moodle Logstore xAPI views events types."""

    COURSE_VIEWED = Events.COURSE_VIEWED
    ACTIVITY_VIEWED = Events.ACTIVITY_VIEWED
    ACTIVITY_MANAGEMENT_VIEWED = Events.ACTIVITY_MANAGEMENT_VIEWED
    RECORDING_VIEWED = Events.RECORDING_VIEWED
    BOOK_MODULE_VIEWED = Events.BOOK_MODULE_VIEWED
    CHAPTER_VIEWED = Events.CHAPTER_VIEWED
    CHAT_MODULE_VIEWED = Events.CHAT_MODULE_VIEWED
    CHOICE_MODULE_VIEWED = Events.CHOICE_MODULE_VIEWED
    DATA_MODULE_VIEWED = Events.DATA_MODULE_VIEWED
    FACETOFACE_MODULE_VIEWED = Events.FACETOFACE_MODULE_VIEWED
    FEEDBACK_MODULE_VIEWED = Events.FEEDBACK_MODULE_VIEWED
    RESPONSE_SUBMITTED = Events.RESPONSE_SUBMITTED
    FOLDER_MODULE_VIEWED = Events.FOLDER_MODULE_VIEWED
    FORUM_MODULE_VIEWED = Events.FORUM_MODULE_VIEWED
    DISCUSSION_VIEWED = Events.DISCUSSION_VIEWED
    USER_REPORT_VIEWED = Events.USER_REPORT_VIEWED
    GLOSSARY_MODULE_VIEWED = Events.GLOSSARY_MODULE_VIEWED
    IMSCP_MODULE_VIEWED = Events.IMSCP_MODULE_VIEWED
    LESSON_MODULE_VIEWED = Events.LESSON_MODULE_VIEWED
    LTI_MODULE_VIEWED = Events.LTI_MODULE_VIEWED
    PAGE_MODULE_VIEWED = Events.PAGE_MODULE_VIEWED
    QUIZ_MODULE_VIEWED = Events.QUIZ_MODULE_VIEWED
    ATTEMPT_VIEWED = Events.ATTEMPT_VIEWED
    RESOURCE_MODULE_VIEWED = Events.RESOURCE_MODULE_VIEWED
    SCORM_MODULE_VIEWED = Events.SCORM_MODULE_VIEWED
    SURVEY_MODULE_VIEWED = Events.SURVEY_MODULE_VIEWED
    URL_MODULE_VIEWED = Events.URL_MODULE_VIEWED
    WIKI_MODULE_VIEWED = Events.WIKI_MODULE_VIEWED
    PAGE_VIEWED = Events.PAGE_VIEWED
    WORKSHOP_MODULE_VIEWED = Events.WORKSHOP_MODULE_VIEWED


class ViewsActivities(Enum):
    """Moodle activities views' types."""

    ASSIGNMENT = Activities.ASSIGNMENT
    LIVE_SESSION = Activities.LIVE_SESSION
    BOOK = Activities.BOOK
    CHAT = Activities.CHAT
    CHOICE = Activities.CHOICE
    DATA = Activities.DATA
    MEETING = Activities.MEETING
    FEEDBACK = Activities.FEEDBACK
    FOLDER = Activities.FOLDER
    FORUM = Activities.FORUM
    GLOSSARY = Activities.GLOSSARY
    IMCSP = Activities.IMCSP
    LESSON = Activities.LESSON
    LTI = Activities.LTI
    PAGE = Activities.PAGE
    QUIZ = Activities.QUIZ
    RESOURCE = Activities.RESOURCE
    SCORM = Activities.SCORM
    SURVEY = Activities.SURVEY
    URL = Activities.URL
    WIKI = Activities.WIKI
    WORKSHOP = Activities.WORKSHOP
