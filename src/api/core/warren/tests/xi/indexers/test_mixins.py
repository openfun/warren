"""Tests for indexers' Mixins."""


import pytest

from warren.xi.indexers.mixins import LangStringMixin


def test_lang_string_mixin():
    """Test 'LangStringMixin' mixin to build a 'LangString' object."""
    mixin_instance = LangStringMixin()

    # Attempt building a 'LangString' without any language
    with pytest.raises(ValueError, match="Language information is missing"):
        mixin_instance.build_lang_string("foo.")

    # Attempt building a 'LangString' while passing a language
    assert mixin_instance.build_lang_string("foo.", "fr") == {"fr": "foo."}

    # Set internal mixin's language for testing
    mixin_instance.language = "en"

    # Attempt building a 'LangString' without passing a language
    assert mixin_instance.build_lang_string("foo.") == {"en": "foo."}

    # Attempt building a 'LangString' with a 'None' value
    assert mixin_instance.build_lang_string(None) == {}
