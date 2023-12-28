"""Experience Index clients with external API."""

from typing import Protocol

from ..client import Client


class LMS(Client, Protocol):
    """Client class for interacting with an LMS API."""

    url: str

    async def get_courses(self, *args, **kwargs):
        """Retrieve a list of courses from an LMS."""
        ...

    async def get_course_contents(self, *args, **kwargs):
        """Retrieve course contents for a specific course from an LMS."""
        ...
