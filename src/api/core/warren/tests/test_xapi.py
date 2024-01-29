"""Test xAPI transformers."""

import pandas as pd

from warren.factories.base import BaseXapiStatementFactory
from warren.xapi import StatementsTransformer


def test_statements_transformer_normalize():
    """Test the normalization of 2 simple statements."""
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]

    statements = StatementsTransformer.normalize(raw_statements)

    assert type(statements) is pd.DataFrame
    assert len(statements) == len(raw_statements)


def test_statements_transformer_to_datetime():
    """Test the parsing of 2 simple statements, with the addition of a "date" column."""
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-01T00:10:00.000000+00:00"}]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[{"timestamp": "2023-01-03T00:10:00.000000+00:00"}]
        ).dict(),
    ]

    statements = StatementsTransformer.normalize(raw_statements)
    statements = StatementsTransformer.to_datetime(statements)

    assert type(statements) is pd.DataFrame
    assert len(statements) == len(raw_statements)
    assert statements["timestamp"].equals(
        pd.to_datetime(
            pd.Series(
                [
                    "2023-01-01T00:10:00.000000+00:00",
                    "2023-01-03T00:10:00.000000+00:00",
                ],
                name="timestamp",
            )
        )
    )


def test_statements_transformer_add_actor_uid():
    """Test the generation of a `actor.uid` column.

    Builds a list of xAPI statements with various identification methods (See the 4
    IFIs of the spec
    https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4), and ensure
    the UID is created properly, and is the same for two equal actors.
    """
    raw_statements = [
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

    statements = StatementsTransformer.normalize(raw_statements)
    statements = StatementsTransformer.to_datetime(statements)
    statements = StatementsTransformer.add_actor_uid_column(statements)

    assert type(statements) == pd.DataFrame
    assert "actor.uid" in statements.columns
    assert statements["actor.uid"].notna
    # Check that 2 identical actors have the same UID
    ids_john = statements[statements["actor.account.name"] == "John"]["actor.uid"]
    assert len(ids_john) == 2
    # Make sure these ids are UID.
    assert len(ids_john.unique()) == 1


def test_statements_transformer_preprocess_empty_statements():
    """Test the preprocess_statements method of the PreprocessMixin.

    Statements sent as arguments are None or an empty list.
    """
    assert StatementsTransformer.preprocess([]) is None
    assert StatementsTransformer.preprocess(None) is None


def test_statements_transformer_preprocess_statements_workflow():
    """Test the preprocess_statements method of the PreprocessMixin."""
    raw_statements = [
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    },
                    "timestamp": "2023-01-01T00:10:00.000000+00:00",
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "account": {"name": "John", "homePage": "http://fun-mooc.fr"},
                    },
                    "timestamp": "2023-01-02T00:10:00.000000+00:00",
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "mbox_sha1sum": "ad85f8d83c1bc6dc8dc1dac26aff567b60e05c16",
                    },
                    "timestamp": "2023-01-02T00:10:00.000000+00:00",
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "objectType": "Agent",
                        "mbox": "mailto:info@xapi.com",
                    },
                    "timestamp": "2023-01-03T00:10:00.000000+00:00",
                }
            ]
        ).dict(),
        BaseXapiStatementFactory.build(
            mutations=[
                {
                    "actor": {
                        "openid": "http://tyler.openid.example.com",
                        "objectType": "Agent",
                    },
                    "timestamp": "2023-01-03T00:10:00.000000+00:00",
                }
            ]
        ).dict(),
    ]

    statements = StatementsTransformer.preprocess(raw_statements)

    assert type(statements) == pd.DataFrame
    assert "actor.uid" in statements.columns
    assert statements["actor.uid"].notna
    assert statements["timestamp"].equals(
        pd.to_datetime(
            pd.Series(
                [
                    "2023-01-01T00:10:00.000000+00:00",
                    "2023-01-02T00:10:00.000000+00:00",
                    "2023-01-02T00:10:00.000000+00:00",
                    "2023-01-03T00:10:00.000000+00:00",
                    "2023-01-03T00:10:00.000000+00:00",
                ],
                name="timestamp",
            )
        )
    )
    # Check that 2 identical actors have the same UID
    ids_john = statements[statements["actor.account.name"] == "John"]["actor.uid"]
    assert len(ids_john) == 2
    # Make sure these ids are UID.
    assert len(ids_john.unique()) == 1
