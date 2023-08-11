from abc import ABC, abstractmethod
import logging

import psycopg2

from warren.conf import settings

logger = logging.getLogger(__name__)

class DatabaseManager(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def execute_query(self, query, params=None):
        pass


class PgsqlManager(DatabaseManager):
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        if self.connection:
            return
        try:
            self.connection = psycopg2.connect(
                user=settings.POSTGRES_INDICATORS_USER,
                password=settings.POSTGRES_INDICATORS_PASSWORD,
                host=settings.POSTGRES_INDICATORS_HOST,
                port=settings.POSTGRES_INDICATORS_PORT,
                database=settings.POSTGRES_INDICATORS_DATABASE
            )
            self.cursor = self.connection.cursor()
        except (Exception, psycopg2.Error) as error:
            logger.error("Error while connecting to PostgreSQL:", error)

    def disconnect(self):
        if not self.connection:
            return
        self.cursor.close()
        self.connection.close()
        self.connection = None
        self.cursor = None

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except (Exception, psycopg2.Error) as error:
            logger.error("Error executing query:", error)
            self.connection.rollback()