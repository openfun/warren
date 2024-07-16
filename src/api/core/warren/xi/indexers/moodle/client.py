"""Moodle HTTP client."""

from typing import List, Optional

from httpx import AsyncClient, ReadTimeout
from pydantic import parse_obj_as

from warren.conf import settings

from ..clients import LMS
from ..exceptions import IndexerQueryException
from .models import Course, Section


class Moodle(LMS):
    """Client class for interacting with Moodle's Web Services."""

    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        """Initialize the Moodle HTTP client."""
        self.url = url or settings.XI_LMS_BASE_URL
        self._token = token or settings.XI_LMS_API_TOKEN
        self.timeout = timeout or settings.XI_LMS_REQUEST_TIMEOUT

        self._client = AsyncClient(
            base_url=f"{self.url}/webservice/rest/server.php",
            params={"wstoken": self._token, "moodlewsrestformat": "json"},
            timeout=self.timeout,
        )

    async def close(self):
        """Close the asynchronous HTTP client."""
        await self._client.aclose()

    async def _get(self, wsfunction: str, **kwargs) -> dict:
        """Get data from Moodle Web Services.

        Args:
            wsfunction (str): Name of the Moodle web service function.
            **kwargs: Additional keyword arguments for the request.

        Returns:
            dict: JSON response from the API as a dictionary.
        """
        try:
            response = await self._client.post(
                "/", data={"wsfunction": wsfunction, **kwargs}
            )
            response.raise_for_status()
        except ReadTimeout as exc:
            raise IndexerQueryException(
                "Timed out while receiving data from the host. Try increasing the "
                "request timeout."
            ) from exc

        # As Moodle's response has a 200 HTTP code when an exception occurs, we
        # need to check the response content instead of only raising for status.
        api_response = response.json()
        if "exception" in api_response:
            raise IndexerQueryException(
                (
                    "An error occurred while querying Moodle API. Error was: "
                    f"[{api_response['errorcode']}] {api_response['message']}"
                )
            )
        return api_response

    async def get_courses(self) -> List[Course]:
        """Retrieve a list of courses from Moodle."""
        raw = await self._get("core_course_get_courses")
        return parse_obj_as(List[Course], raw)

    async def get_course_contents(self, course_id: int) -> List[Section]:
        """Retrieve course contents for a specific course from Moodle."""
        raw = await self._get("core_course_get_contents", courseid=course_id)
        return parse_obj_as(List[Section], raw)
