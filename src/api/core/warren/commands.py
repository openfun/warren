"""warren-api script."""

import argparse
import copy
import sys
from typing import List

from warren import migrations


def get_command_line_parser():
    """Get command line arguments parser."""
    parser = argparse.ArgumentParser(prog="warren")

    # Migrations
    alembic = parser.add_subparsers(title="Database migrations")

    current = alembic.add_parser("current", help="display the current migration")
    current.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="verbose mode",
    )
    current.set_defaults(func=migrations.current, verbose=False)
    downgrade = alembic.add_parser(
        "downgrade", help="downgrade to a specific migration"
    )
    downgrade.add_argument(
        "revision", type=str, help="the target migration to downgrade to"
    )
    downgrade.set_defaults(func=migrations.downgrade)
    history = alembic.add_parser("history", help="display migrations history")
    history.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="verbose mode",
    )
    history.set_defaults(func=migrations.history, verbose=False)
    upgrade = alembic.add_parser("upgrade", help="upgrade to a specific migration")
    upgrade.add_argument(
        "revision",
        type=str,
        default="head",
        nargs="?",
        help="the target migration to upgrade to (default: head)",
    )
    upgrade.set_defaults(func=migrations.upgrade)

    return parser


def main(cmd: List[str]):
    """Warren command line."""
    parser = get_command_line_parser()
    args = parser.parse_args(cmd)
    params = vars(copy.copy(args))

    if not params:
        parser.print_help()

    if hasattr(args, "func"):
        del params["func"]
        args.func(**params)


if __name__ == "__main__":
    main(sys.argv)
