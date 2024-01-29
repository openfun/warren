"""Experience Index indexers Mixins."""

from typing import Optional, Union


class LangStringMixin:
    """Mixin to build LangString object."""

    language: Optional[str]

    def build_lang_string(
        self, value: Union[str, None], language: Optional[str] = None
    ):
        """Build a LangString object."""
        if hasattr(self, "language"):
            language = language or self.language

        if language is None:
            raise ValueError("Language information is missing")

        if value is None:
            return {}

        return {language: value}
