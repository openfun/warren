"""xAPI data transformers."""
import hashlib
from typing import List

import pandas as pd

from warren.conf import settings
from warren.models import XAPI_STATEMENT
from warren.utils import pipe


class StatementsTransformer:
    """xAPI statements transformer.

    This class provides methods to parse LRS statements, add a 'date' column,
    and add an 'actor.uid' column that uniquely identifies the agent.
    It also includes a method to preprocess the statements and apply all
    the necessary transformations all at once.
    """

    @staticmethod
    def normalize(statements: List[XAPI_STATEMENT]) -> pd.DataFrame:
        """Parse LRS statements to a Pandas dataframe. All fields are columns."""
        return pd.json_normalize(statements)

    @staticmethod
    def to_datetime(statements: pd.DataFrame) -> pd.DataFrame:
        """Convert statement's timestamp from string to datetime."""
        statements = statements.copy()
        statements["timestamp"] = pd.to_datetime(statements["timestamp"])
        return statements

    @staticmethod
    def add_actor_uid_column(statements: pd.DataFrame) -> pd.DataFrame:
        """Add a 'actor.uid' column that uniquely identifies the agent.

        Depending on the xAPI statements, the actor can be identified in 4 ways:
        https://github.com/adlnet/xAPI-Spec/blob/master/xAPI-Data.md#details-4. This
        function handles the 4 cases and creates a `uid` column that can be used later
        without worrying about the 4 IFIs.
        """
        statements = statements.copy()
        xapi_actor_identifier_columns = (
            settings.XAPI_ACTOR_IDENTIFIER_PATHS.intersection(statements.columns)
        )

        if not xapi_actor_identifier_columns:
            raise ValueError(
                "There is no way of identifying the agent in submitted statements."
            )

        def get_uid(row):
            return hashlib.sha256(
                "-".join(
                    str(row[col]) for col in xapi_actor_identifier_columns
                ).encode()
            ).hexdigest()

        statements["actor.uid"] = statements.apply(get_uid, axis=1)
        return statements

    @staticmethod
    def preprocess(statements: List[XAPI_STATEMENT]) -> pd.DataFrame:
        """Normalize raw statements, and add utility columns."""
        return pipe(
            StatementsTransformer.normalize,
            StatementsTransformer.add_actor_uid_column,
            StatementsTransformer.to_datetime,
        )(statements)
