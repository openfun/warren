from abc import ABC, abstractmethod

import psycopg2

from warren.conf import settings


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

    @abstractmethod
    def fetch_all(self, query, params=None):
        pass

    @abstractmethod
    def fetch_one(self, query, params=None):
        pass

    @abstractmethod
    def insert(self, table_name, columns, values):
        pass

    @abstractmethod
    def read(self, table_name, where=None):
        pass

    @abstractmethod
    def update(self, table_name, set_column_values, where):
        pass

    @abstractmethod
    def delete(self, table_name, where):
        pass


class PgsqlManager(DatabaseManager):
    def __init__(self):
        self.connection = None
        self.cursor = None

    def connect(self):
        if not self.connection:
            try:
                self.connection = psycopg2.connect(
                    user=settings.POSTGRES_INDICATORS_USER,
                    password=settings.POSTGRES_INDICATORS_PASSWORD,
                    host="postgresql-indicators",
                    port=settings.POSTGRES_INDICATORS_PORT,
                    database="postgres"
                )
                self.cursor = self.connection.cursor()
            except (Exception, psycopg2.Error) as error:
                print("Error while connecting to PostgreSQL:", error)

    def disconnect(self):
        if self.connection:
            self.cursor.close()
            self.connection.close()
            self.connection = None
            self.cursor = None

    def execute_query(self, query, params=None):
        try:
            self.cursor.execute(query, params)
            self.connection.commit()
        except (Exception, psycopg2.Error) as error:
            print("Error executing query:", error)
            self.connection.rollback()

    def fetch_all(self, query, params=None):
        self.execute_query(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=None):
        self.execute_query(query, params)
        return self.cursor.fetchone()

    def insert(self, table_name, columns, values):
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(['%s' for _ in values])})"
        self.execute_query(query, values)

    def read(self, table_name, where=None):
        query = f"SELECT * FROM {table_name}"
        if where:
            query += f" WHERE {where}"
        return self.fetch_all(query)

    def update(self, table_name, set_column_values, where):
        set_clause = ", ".join([f"{column} = %s" for column in set_column_values.keys()])
        values = list(set_column_values.values())
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where}"
        self.execute_query(query, values)

    def delete(self, table_name, where):
        query = f"DELETE FROM {table_name} WHERE {where}"
        self.execute_query(query)
