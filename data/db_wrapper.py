import sqlite3
import datetime


DEBUG = True
DATABASE = "data/bikes.db"
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
def logger(msg="", error=False):
    if (DEBUG or error):
        now = datetime.datetime.now()
        if msg == "":
            print()
        else:
            print(f"{now.strftime('%Y-%m-%d %H:%M:%S')}: {msg}")


def error(msg):
    e = f"ERROR: {msg}"
    logger(e, True)


class Db:

    def __init__(self, name=DATABASE):
        self._conn = sqlite3.connect(name)
        self._conn.row_factory = dict_factory
        self._cursor = self._conn.cursor()


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def connection(self):

        return self._conn

    @property
    def cursor(self):
        return self._cursor

    def commit(self):
        self.connection.commit()

    def close(self, commit=True):
        if commit:
            self.commit()
        self.connection.close()

    def execute(self, sql, params=None):
        self.cursor.execute(sql, params or ())

    def insert(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.cursor.lastrowid

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def query(self, sql, params=None):
        self.cursor.execute(sql, params or ())
        return self.fetchall()
