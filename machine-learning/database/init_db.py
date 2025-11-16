import psycopg2
import os
import sys
from psycopg2.extensions import connection

DB_NAME = os.environ.get('PG_DB', 'redline_db' )
DB_USER = os.environ.get('PG_USER', 'admin' )
DB_PASS = os.environ.get('PG_PASS', 'admin')
DB_HOST = os.environ.get('PG_HOST', 'localhost')
DB_PORT = os.environ.get('PG_PORT', '5432')

def get_db_connection() -> connection:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error: Could not connect to database '{DB_NAME}' as user '{DB_USER}'")
        print(f"Details: {e}")
        sys.exit(1)

def initialize_schema():
    drop_statements = [
        "DROP TABLE IF EXISTS qualifying CASCADE",
        "DROP TABLE IF EXISTS results CASCADE",
        "DROP TABLE IF EXISTS races CASCADE",
        "DROP TABLE IF EXISTS constructors CASCADE",
        "DROP TABLE IF EXISTS drivers CASCADE",
        "DROP TABLE IF EXISTS circuits CASCADE",
    ]

    create_statements = [
        """
        CREATE TABLE IF NOT EXISTS circuits (
            circuitId TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            location TEXT,
            country TEXT
            )
        """,
        """
        CREATE TABLE IF NOT EXISTS drivers (
            driverId TEXT PRIMARY KEY,
            code TEXT,
            givenName TEXT,
            familyName TEXT,
            nationality TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS constructors (
            constructorId TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            nationality TEXT
        ) 
        """,
        """
        CREATE TABLE IF NOT EXISTS races (
            year INTEGER NOT NULL,
            round INTEGER NOT NULL,
            circuitId TEXT NOT NULL,
            name TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            PRIMARY KEY (year, round),
            FOREIGN KEY (circuitId) REFERENCES circuits (circuitId)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS results (
            resultId SERIAL PRIMARY KEY,
            race_year INTEGER NOT NULL,
            race_round INTEGER NOT NULL,
            session_type TEXT NOT NULL,
            driverId TEXT NOT NULL,
            constructorId TEXT NOT NULL,
            grid INTEGER NOT NULL,
            position INTEGER,
            points REAL NOT NULL,
            status TEXT,
            FOREIGN KEY (race_year, race_round) REFERENCES races (year, round),
            FOREIGN KEY (driverId) REFERENCES drivers (driverId),
            FOREIGN KEY (constructorId) REFERENCES constructors (constructorId),
            UNIQUE (race_year, race_round, session_type, driverId)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS qualifying (
            qualifyId SERIAL PRIMARY KEY,
            race_year INTEGER NOT NULL,
            race_round INTEGER NOT NULL,
            session_type TEXT NOT NULL,
            driverId TEXT NOT NULL,
            constructorId TEXT NOT NULL,
            position INTEGER NOT NULL,
            q1 TEXT,
            q2 TEXT,
            q3 TEXT,
            FOREIGN KEY (race_year, race_round) REFERENCES races (year, round),
            FOREIGN KEY (driverId) REFERENCES drivers (driverId),
            FOREIGN KEY (constructorId) REFERENCES constructors (constructorId),
            UNIQUE (race_year, race_round, session_type, driverId)
        )
        """
    ]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                print("Initializing schema")
                print("Dropping old tables")
                for statement in drop_statements:
                    cur.execute(statement)

                print("Creating tables")
                for statement in create_statements:
                    cur.execute(statement)

                print(f"Database schema for '{DB_NAME}' created'")

    except (Exception, psycopg2.DatabaseError) as e:
        print(f"Error during schema initialization: {e}")
        print("Transaction rolled back")

if __name__ == '__main__':
    initialize_schema()