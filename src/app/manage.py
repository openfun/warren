#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "warren.settings")
    os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

    # pylint: disable=import-outside-toplevel
    from configurations.management import execute_from_command_line  # noqa

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
