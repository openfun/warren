"""Moodle HTTP client."""

from typing import List, Optional

from httpx import AsyncClient
from pydantic import parse_obj_as

from warren.conf import settings

from ..clients import LMS
from .models import Course, Section


class Moodle(LMS):
    """Client class for interacting with Moodle's Web Services."""

    def __init__(self, url: Optional[str] = None, token: Optional[str] = None):
        """Initialize the Moodle HTTP client."""
        self.url = url or settings.MOODLE_BASE_URL
        self._token = token or settings.MOODLE_WS_TOKEN

        self._client = AsyncClient(
            base_url=f"{self.url}/webservice/rest/server.php",
            params={"wstoken": self._token, "moodlewsrestformat": "json"},
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
        response = await self._client.post(
            "/", data={"wsfunction": wsfunction, **kwargs}
        )
        response.raise_for_status()
        return response.json()

    async def get_courses(self) -> List[Course]:
        """Retrieve a list of courses from Moodle."""
        raw = await self._get("core_course_get_courses")
        return parse_obj_as(List[Course], raw)

    async def get_course_contents(self, course_id: int) -> List[Section]:
        """Retrieve course contents for a specific course from Moodle."""
        raw = await self._get("core_course_get_contents", courseid=course_id)
        return parse_obj_as(List[Section], raw)
