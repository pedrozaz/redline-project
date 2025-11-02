import psycopg2
import sys
import os
import logging

# DATABASE CONFIG
DB_NAME = os.getenv("DB_NAME", "redline_db")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASS = os.getenv("DB_PASS", "admin")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
# ----------------

def get_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT,
        )
        logging.info(f"Connected to {DB_NAME} database on host {DB_HOST}.")
        return conn
    except psycopg2.OperationalError as e:
        logging.error(f"Failed to connect to {DB_NAME} database on host {DB_HOST}.")
        logging.error(e)
        sys.exit(1)

def create_tables(conn):

    cursor = conn.cursor()
    logging.warning(f"Dropping tables in {DB_NAME} database if exists.")

    cursor.execute(f"DROP TABLE IF EXISTS weather CASCADE;")
    cursor.execute(f"DROP TABLE IF EXISTS drivers CASCADE;")
    cursor.execute(f"DROP TABLE IF EXISTS session_results CASCADE;")
    cursor.execute(f"DROP TABLE IF EXISTS sessions CASCADE;")

    logging.warning(f"Creating tables in {DB_NAME} database.")

    cursor.execute("""
                    CREATE TABLE sessions (
                    session_key INTEGER PRIMARY KEY,
                    session_name TEXT,
                    session_type TEXT,
                    country_name TEXT,
                    circuit_key INTEGER,
                    circuit_short_name TEXT,
                    date_start TIMESTAMP,
                    year INTEGER
                    )
    """)

    cursor.execute("""
                   CREATE TABLE session_results (
                       id SERIAL PRIMARY KEY,
                       session_key INTEGER REFERENCES sessions(session_key) ON DELETE CASCADE,
                       driver_number INTEGER,
                       position INTEGER,
                       points INTEGER,
                       dnf BOOLEAN,
                       dns BOOLEAN,
                       dsq BOOLEAN
                   )
                   """)

    cursor.execute("""
                   CREATE TABLE drivers (
                    driver_number INTEGER,
                    session_key INTEGER REFERENCES sessions(session_key) ON DELETE CASCADE,
                    meeting_key INTEGER,
                    broadcast_name TEXT,
                    full_name TEXT,
                    team_name TEXT,
                    team_colour TEXT,
                    country_code TEXT,
                    PRIMARY KEY (driver_number, session_key)
                   )
                   """)

    cursor.execute("""
                CREATE TABLE weather
                (
                    id SERIAL PRIMARY KEY,
                    session_key INTEGER REFERENCES sessions(session_key) ON DELETE CASCADE,
                    date TIMESTAMP,
                    air_temperature REAL,
                    track_temperature REAL,
                    rainfall INTEGER,
                    humidity REAL,
                    pressure REAL,
                    wind_speed REAL,
                    wind_direction INTEGER
                )
                """)

    conn.commit()
    cursor.close()
    logging.info(f"Created tables in {DB_NAME} database.")

if __name__ == "__main__":
    db_conn = get_connection()
    if db_conn:
        create_tables(db_conn)
        db_conn.close()
        logging.info(f"Connected to {DB_NAME} database on host {DB_HOST}.")

