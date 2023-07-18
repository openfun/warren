"""Test the functions from the BaseIndicator class."""
import pandas as pd

from warren.base_indicator import add_actor_unique_id, parse_raw_statements
from warren.factories.base import BaseXapiStatementFactory


def test_parse_raw_statements():
    """Test the parsing of 2 simple statements, with the addition of a "date" column."""
    statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]

    parsed = parse_raw_statements(statements)
    assert "date" in parsed.columns
    assert parsed["date"].equals(
        pd.to_datetime(pd.Series(["2023-01-01", "2023-01-03"], name="date")).dt.date
    )
    assert len(statements) == len(parsed)


def test_add_actor_unique_id():
    """Test the generation of a `actor.uuid` column.

    Builds a list of xAPI statements with various identification methods (See the 4
    IFIs of the spec
    https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4), and ensure
    the UUID is created properly, and is the same for two equal actors.
    """
    statements = [
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    }
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    }
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "mbox_sha1sum": "ad85f8d83c1bc6dc8dc1dac26aff567b60e05c16",
                    }
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "mbox": "mailto:info@xapi.com",
                    }
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "openid": "http://tyler.openid.example.com",
                        "objectType": "Agent",
                    }
                }
            ]
        ).dict(),
    ]

    statements = parse_raw_statements(statements)
    statements = add_actor_unique_id(statements)
    assert "actor.uuid" in statements.columns
    assert statements["actor.uuid"].notna
    # Check that 2 identical actors have the same UUID
    uuids_john = statements[statements["actor.account.name"] == "John"]["actor.uuid"]
    assert len(uuids_john) == 2
    assert len(uuids_john.unique()) == 1
