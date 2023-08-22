"""Test the functions from the BaseIndicator class."""
import pandas as pd

from warren.factories.base import BaseXapiStatementFactory
from warren.indicators import PreprocessMixin


def test_parse_raw_statements():
    """Test the parsing of 2 simple statements."""
    preprocessing = PreprocessMixin()
    preprocessing.raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]

    preprocessing.parse_raw_statements()

    assert len(preprocessing.statements) == len(preprocessing.raw_statements)


def test_add_date_column():
    """Test the parsing of 2 simple statements, with the addition of a "date" column."""
    preprocessing = PreprocessMixin()
    preprocessing.raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]

    preprocessing.parse_raw_statements()
    preprocessing.add_date_column()

    assert len(preprocessing.statements) == len(preprocessing.raw_statements)
    assert preprocessing.statements["date"].equals(
        pd.to_datetime(pd.Series(["2023-01-01", "2023-01-03"], name="date")).dt.date
    )


def test_add_actor_uid():
    """Test the generation of a `actor.uid` column.

    Builds a list of xAPI statements with various identification methods (See the 4
    IFIs of the spec
    https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4), and ensure
    the UID is created properly, and is the same for two equal actors.
    """
    preprocessing = PreprocessMixin()
    preprocessing.raw_statements = [
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

    preprocessing.parse_raw_statements()
    preprocessing.add_date_column()
    preprocessing.add_actor_uid_column()

    assert "actor.uid" in preprocessing.statements.columns
    assert preprocessing.statements["actor.uid"].notna
    # Check that 2 identical actors have the same UID
    ids_john = preprocessing.statements[
        preprocessing.statements["actor.account.name"] == "John"
    ]["actor.uid"]
    assert len(ids_john) == 2
    # Make sure these ids are UID.
    assert len(ids_john.unique()) == 1
